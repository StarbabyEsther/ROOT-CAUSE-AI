"""Investigation job orchestration.

One job = one disposable workspace + one subprocess + one result. Jobs are held in
memory (they are short-lived and single-machine), while the *limits* are durable
in SQLite.

Safety properties enforced here:
  * the child is launched with the job directory as cwd, so all backend artifacts
    land inside the job and the repository is never written to;
  * the child runs in its own process group and is killed as a group on timeout,
    so a wedged grandchild (e.g. a hung sandbox CLI) cannot outlive the job;
  * every job has a hard wall-clock ceiling;
  * the concurrency slot is released in a `finally`, whatever happens;
  * output is bounded and scrubbed before it is stored or streamed.
"""

from __future__ import annotations

import asyncio
import json
import os
import signal
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable

from .config import SCENARIOS, Settings
from .limits import RateLimiter
from .normalise import build_result, parse_unittest_output
from .redact import SecretScrubber
from .workspace import JobWorkspace, cleanup_workspace, create_workspace

MARKER = "RCAI_"
STAGES = ("investigate", "diagnose", "repair", "verify")

# Where each scenario's candidate repair is written by the backend.
CANDIDATE_PATHS = {
    "duplicate_transaction": "verification_bundle/transactions.py",
    "incorrect_refund": "refund_verification_bundle/refund_processor.py",
    "monetary_precision": "precision_verification_bundle/precision_processor.py",
}


def new_job_id() -> str:
    return uuid.uuid4().hex


def valid_job_id(value: str) -> bool:
    return len(value) == 32 and all(c in "0123456789abcdef" for c in value)


@dataclass
class Job:
    id: str
    scenario_id: str
    ip: str
    status: str = "queued"
    stage: str | None = None
    created_at: float = field(default_factory=time.time)
    finished_at: float | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
    subscribers: list[asyncio.Queue] = field(default_factory=list)
    task: asyncio.Task | None = None

    def publish(self, event: dict[str, Any]) -> None:
        self.events.append(event)
        for queue in list(self.subscribers):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:  # pragma: no cover - bounded queues
                pass

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=256)
        for event in self.events:  # replay so late subscribers see the history
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                break
        self.subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        if queue in self.subscribers:
            self.subscribers.remove(queue)


class JobManager:
    def __init__(
        self,
        settings: Settings,
        limiter: RateLimiter,
        scrubber: SecretScrubber,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.settings = settings
        self.limiter = limiter
        self.scrubber = scrubber
        self._jobs: dict[str, Job] = {}
        self._clock = clock

    # ------------------------------------------------------------------ lookup

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def prune(self) -> None:
        cutoff = self._clock() - self.settings.job_ttl_seconds
        for job_id, job in list(self._jobs.items()):
            if job.status in {"done", "error"} and (job.finished_at or 0) < cutoff:
                self._jobs.pop(job_id, None)

    # ------------------------------------------------------------------- start

    def start(self, scenario_id: str, ip: str) -> tuple[Job | None, str]:
        """Create and schedule a job. Returns (job, reason)."""
        if not self.settings.live_enabled:
            return None, "live_disabled"
        if scenario_id not in SCENARIOS:
            return None, "unknown_scenario"

        job_id = new_job_id()
        decision = self.limiter.check_and_claim(ip, job_id)
        if not decision.allowed:
            return None, decision.reason

        job = Job(id=job_id, scenario_id=scenario_id, ip=ip)
        self._jobs[job_id] = job
        job.task = asyncio.create_task(self._run(job))
        return job, "started"

    # --------------------------------------------------------------------- run

    async def _run(self, job: Job) -> None:
        workspace: JobWorkspace | None = None
        process: asyncio.subprocess.Process | None = None
        try:
            job.status = "running"
            workspace = create_workspace(
                self.settings.backend_dir, self.settings.workspace_root, job.id
            )

            markers: dict[str, Any] = {"events": []}
            stdout_lines: list[str] = []

            command = self._child_command(job.scenario_id, workspace)
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=str(workspace.path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                start_new_session=True,
                env=self._child_env(),
            )

            try:
                await asyncio.wait_for(
                    self._pump(job, process, markers, stdout_lines),
                    timeout=self.settings.child_timeout_seconds,
                )
                await process.wait()
            except asyncio.TimeoutError:
                await self._terminate(process)
                raise RuntimeError(
                    f"Investigation exceeded {self.settings.child_timeout_seconds}s and was stopped."
                )

            result = self._assemble(job, workspace, markers)
            job.result = result.model_dump(by_alias=True)
            job.status = "done"
            job.publish({"type": "result", "data": job.result})

        except Exception as error:  # noqa: BLE001 - reported, never raised to the client raw
            if process is not None:
                await self._terminate(process)
            job.status = "error"
            job.error = self.scrubber.scrub(f"{type(error).__name__}: {error}")
            job.publish({"type": "error", "message": job.error})
        finally:
            job.finished_at = self._clock()
            if workspace is not None:
                cleanup_workspace(workspace)
            self.limiter.release(job.id)

    async def _pump(
        self,
        job: Job,
        process: asyncio.subprocess.Process,
        markers: dict[str, Any],
        stdout_lines: list[str],
    ) -> None:
        assert process.stdout is not None
        async for raw in process.stdout:
            line = self.scrubber.scrub(raw.decode("utf-8", "replace").rstrip("\n"))
            stdout_lines.append(line)
            if len(stdout_lines) > 5000:  # bound memory on a runaway child
                del stdout_lines[: len(stdout_lines) - 5000]

            if line.startswith(MARKER):
                self._handle_marker(job, line, markers)
            else:
                # Real backend tracebacks arrive here, not in the markers.
                markers.setdefault("stdout", []).append(line)

    def _handle_marker(self, job: Job, line: str, markers: dict[str, Any]) -> None:
        try:
            kind, payload = line[len(MARKER):].split(" ", 1)
            data = json.loads(payload)
        except (ValueError, IndexError):
            return

        if kind == "EVENT":
            stage, status = data.get("stage"), data.get("status")
            if stage in STAGES:
                job.stage = stage
                job.publish({"type": "stage", "stage": stage, "status": status})
                markers["events"].append(data)
        elif kind == "FINANCIAL":
            markers["financial"] = data
        elif kind == "RESULT":
            markers["workflow"] = data
        elif kind == "AST":
            markers["ast"] = data
        elif kind == "ERROR":
            markers["error"] = data

    def _assemble(self, job: Job, workspace: JobWorkspace, markers: dict[str, Any]) -> Any:
        financial = markers.get("financial")
        workflow = markers.get("workflow")
        if not financial or not workflow:
            raise RuntimeError(
                "The backend did not return a complete investigation "
                f"({self.scrubber.scrub(str(markers.get('error') or 'missing markers'))})."
            )

        source_file = str(SCENARIOS[job.scenario_id]["source_file"])
        original_path = workspace.path / source_file
        original = original_path.read_text(encoding="utf-8") if original_path.is_file() else ""

        candidate_path = workspace.path / CANDIDATE_PATHS[job.scenario_id]
        candidate = candidate_path.read_text(encoding="utf-8") if candidate_path.is_file() else ""

        patch = self._read_json(workspace.path / "proposed_patch.json")
        baseline_logs = self._measure_baseline(workspace, job.scenario_id)

        return build_result(
            job_id=job.id,
            scenario_id=job.scenario_id,
            financial=financial,
            workflow=workflow,
            patch=patch,
            ast=markers.get("ast"),
            original_source=original,
            candidate_source=candidate,
            baseline_logs=baseline_logs,
            child_logs="\n".join(markers.get("stdout", [])[-500:]),
            max_log_bytes=self.settings.max_log_bytes,
        )

    # ---------------------------------------------------------------- baseline

    def _measure_baseline(self, workspace: JobWorkspace, scenario_id: str) -> str:
        """Run the scenario's own tests against the untouched source.

        This is plain `unittest` over the copied repository — no model, no sandbox.
        It tells the UI which tests the *buggy* file fails, which the backend
        reports do not consistently include.
        """
        test_file = str(SCENARIOS[scenario_id]["test_file"])
        if not (workspace.path / test_file).is_file():
            return ""
        try:
            completed = __import__("subprocess").run(
                [sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", test_file, "-v"],
                cwd=str(workspace.path),
                capture_output=True,
                text=True,
                timeout=90,
            )
            return self.scrubber.scrub(completed.stdout + completed.stderr)
        except Exception as error:  # noqa: BLE001
            return self.scrubber.scrub(f"Baseline could not be measured: {type(error).__name__}")

    # ------------------------------------------------------------------ helpers

    def _child_command(self, scenario_id: str, workspace: JobWorkspace) -> list[str]:
        if self.settings.child_command:
            return [*self.settings.child_command, scenario_id]
        launcher = Path(__file__).resolve().parent / "launcher.py"
        return [sys.executable, str(launcher), scenario_id]

    def _child_env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        # Never inherit a stray variable that would point the backend elsewhere.
        env.pop("PYTHONPATH", None)
        return env

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any] | None:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    @staticmethod
    async def _terminate(process: asyncio.subprocess.Process) -> None:
        if process.returncode is not None:
            return
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            return
        try:
            await asyncio.wait_for(process.wait(), timeout=10)
        except asyncio.TimeoutError:  # pragma: no cover
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass


async def wait_for_job(job: Job) -> None:
    if job.task is not None:
        await asyncio.shield(job.task)


def baseline_counts(text: str) -> dict[str, int]:
    parsed = parse_unittest_output(text)
    return {"ran": parsed["ran"], "failed": parsed["failed"]}


def run_coro(coro: Awaitable[Any]) -> Any:  # pragma: no cover - helper for scripts
    return asyncio.run(coro)  # type: ignore[arg-type]

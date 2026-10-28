"""Preflight — one command to answer "can we go live today?".

Checks, in order, only what can be checked without spending money or running a
model:

  1. configuration present (names only, never values)
  2. the backend's real modules import from a copied workspace
  3. `contree` exists, is authenticable, and lists images
  4. the adapter's own tests pass
  5. (optional) one real end-to-end run, which *does* spend tokens

Usage:
    api/.venv/bin/python -m api.preflight             # safe checks only
    api/.venv/bin/python -m api.preflight --live      # adds a real run

Exit code 0 means "ready". Anything else prints exactly what is missing and whose
job it is to fix it.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

OK = "  OK   "
WARN = "  WARN "
FAIL = "  FAIL "

REPO = Path(__file__).resolve().parent.parent
SECRET_NAMES = ("NEBIUS_API_KEY", "NEBIUS_MODEL", "CONTREE_PROJECT_ID")


class Report:
    def __init__(self) -> None:
        self.failures = 0
        self.warnings = 0

    def ok(self, message: str) -> None:
        print(OK + message)

    def warn(self, message: str, action: str = "") -> None:
        self.warnings += 1
        print(WARN + message + (f"\n         → {action}" if action else ""))

    def fail(self, message: str, action: str = "") -> None:
        self.failures += 1
        print(FAIL + message + (f"\n         → {action}" if action else ""))


def check_config(report: Report) -> None:
    print("\n[1/5] Configuration")
    for name in SECRET_NAMES:
        value = os.getenv(name, "")
        if value:
            report.ok(f"{name} is set ({len(value)} chars)")
        else:
            report.fail(
                f"{name} is not set",
                "add it to your shell or the platform secret store (never commit it)",
            )

    if os.getenv("LIVE_RUNS_ENABLED", "").lower() in {"1", "true", "yes", "on"}:
        report.ok("LIVE_RUNS_ENABLED=true")
    else:
        report.warn(
            "LIVE_RUNS_ENABLED is not true",
            "live investigations will return 503 until you set it",
        )

    state_dir = Path(os.getenv("RC_STATE_DIR", "/tmp/rcai-state"))
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        probe = state_dir / ".write-probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        report.ok(f"RC_STATE_DIR is writable ({state_dir})")
        if str(state_dir).startswith("/tmp"):
            report.warn(
                "RC_STATE_DIR is under /tmp",
                "on Fly.io mount a volume here, or rate limits reset on every deploy",
            )
    except OSError as error:
        report.fail(f"RC_STATE_DIR is not writable: {error}", "create it or point RC_STATE_DIR elsewhere")


def check_backend(report: Report) -> None:
    print("\n[2/5] Backend modules")
    if not (REPO / "workflow.py").is_file():
        report.fail("workflow.py not found", "run this from the repository root")
        return
    report.ok("workflow.py present")

    code = (
        "import sys; sys.path.insert(0, '.');"
        "from workflow import run_workflow;"
        "from financial_investigator import investigate_transactions;"
        "from scenario_registry import get_scenario;"
        "print('imports-ok')"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code], cwd=REPO, capture_output=True, text=True, timeout=120
    )
    if "imports-ok" in completed.stdout:
        report.ok("backend imports cleanly without credentials")
    else:
        report.fail(
            "backend failed to import",
            completed.stderr.strip().splitlines()[-1] if completed.stderr else "see traceback",
        )


def check_contree(report: Report) -> None:
    print("\n[3/5] Nebius sandbox CLI")
    binary = shutil.which("contree")
    if not binary:
        report.fail(
            "contree is not on PATH",
            "pip install contree-cli (already in api/requirements-api.txt for the image)",
        )
        return
    report.ok(f"contree found at {binary}")

    completed = subprocess.run(
        ["contree", "images", "--prefix", "python"],
        capture_output=True,
        text=True,
        timeout=120,
        env=os.environ.copy(),
    )
    if completed.returncode == 0:
        report.ok("contree authentication works and images are listable")
    else:
        tail = (completed.stderr or completed.stdout).strip().splitlines()
        report.fail(
            "contree is installed but not authenticated",
            "run `contree auth --type iam` with CONTREE_PROJECT_ID and NEBIUS_API_KEY set "
            f"(detail: {tail[-1] if tail else 'no output'})",
        )


def check_tests(report: Report) -> None:
    print("\n[4/5] Adapter tests")
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "api/tests"],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=900,
    )
    if completed.returncode == 0:
        last = [line for line in completed.stdout.strip().splitlines() if "passed" in line]
        report.ok(last[-1] if last else "adapter tests pass")
    else:
        report.fail("adapter tests fail, fix before deploying", completed.stdout.strip()[-400:])


def check_live(report: Report) -> None:
    print("\n[5/5] Live end-to-end run (this spends tokens)")
    from api.config import Settings
    from api.jobs import JobManager
    from api.limits import RateLimiter
    from api.redact import SecretScrubber

    settings = Settings.from_env()
    if not settings.live_enabled:
        report.warn("skipped: LIVE_RUNS_ENABLED is false")
        return

    import asyncio
    import tempfile

    async def run_once() -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings_override = Settings(
                live_enabled=True,
                limits=settings.limits,
                state_dir=Path(tmp) / "state",
                workspace_root=Path(tmp) / "work",
                backend_dir=REPO,
                child_command=None,
            )
            limiter = RateLimiter(settings_override.state_dir / "limits.sqlite3", settings_override.limits)
            manager = JobManager(
                settings_override, limiter, SecretScrubber(settings_override.secret_values())
            )
            job, reason = manager.start("duplicate_transaction", "127.0.0.1")
            if job is None:
                report.fail(f"could not start a run ({reason})")
                return
            assert job.task is not None
            await asyncio.wait_for(job.task, timeout=settings_override.child_timeout_seconds)

            if job.status != "done" or not job.result:
                report.fail(f"live run failed: {job.error or 'no result'}")
                return

            verification = job.result["verification"]
            verdict = verification["verdict"]
            passed = verification["reference"]["passed"]
            expected = verification["expectedTests"]
            if verdict == "verified_fixed" and passed == expected:
                report.ok(f"live run verified: {passed}/{expected} tests passed in the sandbox")
            else:
                report.fail(
                    f"live run did not verify (verdict={verdict}, passed={passed}/{expected})",
                    "check the sandbox logs before showing this publicly",
                )

    asyncio.run(run_once())


def main() -> int:
    parser = argparse.ArgumentParser(description="RootCause AI go-live preflight")
    parser.add_argument("--live", action="store_true", help="also perform one real investigation")
    args = parser.parse_args()

    print("RootCause AI — preflight")
    print("=" * 58)
    report = Report()
    check_config(report)
    check_backend(report)
    check_contree(report)
    check_tests(report)
    if args.live:
        check_live(report)
    else:
        print("\n[5/5] Live end-to-end run — skipped (pass --live to enable; spends tokens)")

    print("\n" + "=" * 58)
    if report.failures:
        print(f"NOT READY — {report.failures} blocker(s), {report.warnings} warning(s)")
        return 1
    print(f"READY — 0 blockers, {report.warnings} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Child-process launcher.

Executed *inside* a job workspace (cwd = the per-job copy) so that
`workflow.ROOT` resolves to that copy and every artifact the backend writes lands
in the job directory.

It calls the existing, unmodified `workflow.run_workflow()` — the documented seam
— and reports progress back to the adapter over stdout using an `RCAI_` marker
protocol. It never imports the model client into the server process, and it never
modifies the backend.

Stage reporting is deliberately conservative. `run_workflow` captures its own
child's output, so stages 2–4 become visible only when it returns; the adapter is
told the backend phase has started and is given the real outcomes afterwards.

Markers (one JSON object per line on stdout):
    RCAI_EVENT     {"stage": "...", "status": "running"|"done"}
    RCAI_FINANCIAL {...}   verify of the deterministic investigation
    RCAI_AST       {"passed": bool, "reason": str, "negativeControl": {...}}
    RCAI_RESULT    the run_workflow() dict
    RCAI_ERROR     {"message": "..."} on an unexpected failure
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import traceback
from pathlib import Path

MARKER = "RCAI_"
# Keep each marker line bounded so a huge report cannot break line scanning.
MAX_MARKER_BYTES = 2_000_000


def emit(kind: str, payload: object) -> None:
    line = f"{MARKER}{kind} {json.dumps(payload, default=str)}"
    if len(line) > MAX_MARKER_BYTES:
        line = json.dumps({"truncated": True, "bytes": len(line)})
        line = f"{MARKER}{kind} {line}"
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def emit_event(stage: str, status: str) -> None:
    emit("EVENT", {"stage": stage, "status": status})


def run_ast_probe(source_file: str, patch: dict | None) -> dict:
    """Run the project's own patch_validator on the real patch and a control.

    Executed in a throwaway directory so `proposed_patch.json` in the job is never
    overwritten. No model call, no sandbox, no network.
    """
    result = {
        "passed": False,
        "reason": "No candidate patch was produced for this run.",
        "negativeControl": {"passed": True, "reason": "Control patch was not evaluated."},
    }
    if not patch:
        return result

    original = Path(source_file)
    if not original.is_file():
        result["reason"] = f"Source file {source_file} not found in workspace."
        return result

    try:
        from patch_validator import validate_patch  # noqa: PLC0415 — job-local import

        with tempfile.TemporaryDirectory() as scratch:
            scratch_path = Path(scratch)
            (scratch_path / source_file).write_text(original.read_text(encoding="utf-8"), encoding="utf-8")
            (scratch_path / "proposed_patch.json").write_text(json.dumps(patch), encoding="utf-8")

            previous = os.getcwd()
            os.chdir(scratch_path)
            try:
                passed, reason = validate_patch(source_file)

                control = {
                    "root_cause": "control",
                    "explanation": "control",
                    "target_file": source_file,
                    "proposed_code": (
                        "def calculate_total(transactions):\n"
                        "    return 0\n\n"
                        "def helper():\n"
                        "    return 1\n"
                    ),
                }
                (scratch_path / "proposed_patch.json").write_text(json.dumps(control), encoding="utf-8")
                control_passed, control_reason = validate_patch(source_file)
            finally:
                os.chdir(previous)

        result["passed"] = bool(passed)
        result["reason"] = str(reason)
        # `passed` here means the *control was accepted*. A healthy gate rejects it,
        # so a correct negative control reports passed=False.
        result["negativeControl"] = {"passed": bool(control_passed), "reason": str(control_reason)}
    except Exception as error:  # pragma: no cover - defensive
        result["reason"] = f"Structural validation could not be run: {type(error).__name__}"
    return result


def main() -> int:
    if len(sys.argv) < 2:
        emit("ERROR", {"message": "Usage: launcher.py <scenario_id>"})
        return 2

    scenario_id = sys.argv[1]

    # The job directory is the working directory, and it is what must satisfy the
    # backend's own imports — not this file's location.
    job_dir = Path.cwd()
    sys.path.insert(0, str(job_dir))
    os.environ.setdefault("PYTHONUNBUFFERED", "1")

    try:
        from financial_investigator import investigate_transactions  # noqa: PLC0415
        from scenario_registry import get_scenario  # noqa: PLC0415

        emit_event("investigate", "running")
        scenario = get_scenario(scenario_id)
        financial = investigate_transactions(
            scenario["records"], calculator=scenario["calculator"]
        )
        emit("FINANCIAL", financial)
        emit_event("investigate", "done")

        # Stages 2–4 all happen inside run_workflow; report the phase as running now.
        emit_event("diagnose", "running")

        from workflow import run_workflow  # noqa: PLC0415

        outcome = run_workflow(scenario_id)
        emit("RESULT", outcome)

        emit_event("diagnose", "done")
        emit_event("repair", "done")
        emit_event("verify", "done")

        patch_path = job_dir / "proposed_patch.json"
        patch = None
        if patch_path.is_file():
            try:
                patch = json.loads(patch_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                patch = None

        emit("AST", run_ast_probe(str(scenario["source_file"]), patch))
        return 0

    except Exception as error:
        emit("ERROR", {"message": f"{type(error).__name__}: {error}"})
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

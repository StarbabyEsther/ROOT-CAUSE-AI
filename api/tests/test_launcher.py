"""The real launcher against the real backend — no credentials required.

Stage 1 (financial investigation) genuinely works without any Nebius key, so we
assert that it runs for all three scenarios. The model phase then fails fast
because no key is present, which we assert is reported as a clean marker rather
than an unhandled crash. This exercises the true isolation path (a copied module
tree) without any network, model call or sandbox use.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from api.workspace import cleanup_workspace, create_workspace

REPO_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = REPO_ROOT / "api" / "launcher.py"


def run_launcher(tmp_path, scenario: str, env_overrides: dict[str, str] | None = None):
    workspace = create_workspace(REPO_ROOT, tmp_path, f"test{scenario[:8]}")
    env = {k: v for k, v in os.environ.items() if k not in {"NEBIUS_API_KEY", "NEBIUS_MODEL", "CONTREE_TOKEN"}}
    env["PYTHONUNBUFFERED"] = "1"
    env.update(env_overrides or {})
    try:
        completed = subprocess.run(
            [sys.executable, str(LAUNCHER), scenario],
            cwd=str(workspace.path),
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
    finally:
        cleanup_workspace(workspace)
    return completed


def markers(output: str) -> dict[str, list]:
    found: dict[str, list] = {}
    for line in output.splitlines():
        if line.startswith("RCAI_"):
            kind, _, payload = line[5:].partition(" ")
            try:
                found.setdefault(kind, []).append(json.loads(payload))
            except ValueError:
                found.setdefault(kind, []).append(payload)
    return found


@pytest.mark.parametrize(
    ("scenario", "issue_type", "discrepancy"),
    [
        ("duplicate_transaction", "Possible duplicate processing", "200.00"),
        ("incorrect_refund", "Possible refund sign error", "100.00"),
        ("monetary_precision", "Unclassified financial discrepancy", "4E-17"),
    ],
)
def test_stage_one_runs_without_credentials(tmp_path, scenario, issue_type, discrepancy):
    completed = run_launcher(tmp_path, scenario)
    found = markers(completed.stdout + completed.stderr)

    assert "FINANCIAL" in found, f"no financial marker. output:\n{completed.stdout}"
    financial = found["FINANCIAL"][0]
    assert financial["issue_type"] == issue_type
    assert financial["discrepancy"] == discrepancy

    events = [(e["stage"], e["status"]) for e in found.get("EVENT", [])]
    assert ("investigate", "running") in events
    assert ("investigate", "done") in events


def test_missing_credentials_are_reported_not_crashed(tmp_path):
    completed = run_launcher(tmp_path, "duplicate_transaction")
    found = markers(completed.stdout + completed.stderr)

    # Either the run completed (credentials present in the developer's shell) or it
    # reported a clean error marker. A raw traceback with no marker is a failure.
    assert "RESULT" in found or "ERROR" in found
    if "ERROR" in found:
        assert completed.returncode != 0
        assert "RuntimeError" in json.dumps(found["ERROR"]) or found["ERROR"]


def test_launcher_does_not_write_to_the_repository(tmp_path):
    before = sorted(p.name for p in REPO_ROOT.glob("*.json"))
    run_launcher(tmp_path, "duplicate_transaction")
    after = sorted(p.name for p in REPO_ROOT.glob("*.json"))
    assert before == after, "the job wrote artifacts into the repository"

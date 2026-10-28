"""Shared fixtures for the M1 adapter tests.

All execution is simulated: `fake_child.py` speaks the same `RCAI_` marker
protocol as the real launcher and writes the same artifacts, so the adapter is
exercised end to end with no credentials, no model calls and no sandbox use.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from api.config import Limits, Settings  # noqa: E402
from api.redact import SecretScrubber  # noqa: E402

FAKE_CHILD = Path(__file__).resolve().parent / "fake_child.py"
TEST_SECRET = "nebius-SECRET-key-0123456789abcdef"


@pytest.fixture
def secrets_env(monkeypatch):
    monkeypatch.setenv("NEBIUS_API_KEY", TEST_SECRET)
    monkeypatch.setenv("NEBIUS_MODEL", "nvidia/Nemotron-Test-Only")
    monkeypatch.setenv("CONTREE_PROJECT_ID", "project-test-0001")
    return TEST_SECRET


@pytest.fixture
def settings(tmp_path, secrets_env) -> Settings:
    return Settings(
        live_enabled=True,
        limits=Limits(per_ip_hour=2, per_ip_day=5, global_day=30, max_concurrent=1),
        state_dir=tmp_path / "state",
        workspace_root=tmp_path / "work",
        backend_dir=REPO_ROOT,
        allowed_origins=("http://localhost:5173",),
        child_timeout_seconds=30,
        child_command=(sys.executable, str(FAKE_CHILD)),
    )


@pytest.fixture
def scrubber(secrets_env) -> SecretScrubber:
    return SecretScrubber([TEST_SECRET])


@pytest.fixture
def client(settings, scrubber):
    from fastapi.testclient import TestClient

    from api.main import create_app

    app = create_app(settings=settings, scrubber=scrubber)
    with TestClient(app) as test_client:
        test_client.app_ref = app  # type: ignore[attr-defined]
        yield test_client


def wait_for(client, job_id: str, timeout: float = 25.0) -> dict:
    """Poll until the job leaves queued/running."""
    import time

    deadline = time.time() + timeout
    while time.time() < deadline:
        response = client.get(f"/api/investigations/{job_id}")
        assert response.status_code == 200, response.text
        body = response.json()
        if body.get("status") not in {"queued", "running"}:
            return body
        time.sleep(0.05)
    raise AssertionError(f"job {job_id} did not finish within {timeout}s")


def start(client, scenario_id: str = "duplicate_transaction") -> str:
    response = client.post("/api/investigations", json={"scenario_id": scenario_id})
    assert response.status_code == 202, response.text
    return response.json()["id"]


def load_contract_ts() -> str:
    return (REPO_ROOT / "web" / "src" / "lib" / "contract.ts").read_text(encoding="utf-8")


def json_dump(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")

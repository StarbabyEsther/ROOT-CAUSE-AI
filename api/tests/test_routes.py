"""End-to-end route behaviour with a simulated child process."""

from __future__ import annotations

import json

import pytest

from api.config import Limits, Settings
from api.main import create_app
from api.tests.conftest import TEST_SECRET, start, wait_for


class TestHealthAndScenarios:
    def test_health_defaults_to_replay(self, client):
        body = client.get("/api/health").json()
        assert body["ok"] is True
        assert body["liveEnabled"] is True  # enabled in the test settings
        assert body["limits"]["per_ip_hour"] == 2
        assert body["limits"]["global_day"] == 30

    def test_live_disabled_by_default_in_env(self, monkeypatch):
        """Shipping default: live runs off, replay unaffected."""
        settings = Settings.from_env({})
        assert settings.live_enabled is False

    def test_scenarios_lists_three(self, client):
        body = client.get("/api/scenarios").json()
        assert [s["id"] for s in body] == [
            "duplicate_transaction",
            "incorrect_refund",
            "monetary_precision",
        ]
        assert [s["testCount"] for s in body] == [6, 7, 5]

    def test_cors_restricted_to_allowlist(self, client):
        response = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
        response = client.get("/api/health", headers={"Origin": "http://evil.example"})
        assert response.headers.get("access-control-allow-origin") is None


class TestStart:
    def test_unknown_scenario_rejected(self, client):
        response = client.post("/api/investigations", json={"scenario_id": "arbitrary"})
        assert response.status_code == 422  # closed enum, validated by the model

    def test_extra_fields_rejected(self, client):
        response = client.post(
            "/api/investigations",
            json={"scenario_id": "duplicate_transaction", "code": "import os"},
        )
        assert response.status_code == 422

    def test_live_disabled_returns_503(self, settings, scrubber):
        from fastapi.testclient import TestClient

        disabled = Settings(
            live_enabled=False,
            state_dir=settings.state_dir,
            workspace_root=settings.workspace_root,
            backend_dir=settings.backend_dir,
            child_command=settings.child_command,
        )
        with TestClient(create_app(settings=disabled, scrubber=scrubber)) as local:
            response = local.post("/api/investigations", json={"scenario_id": "duplicate_transaction"})
            assert response.status_code == 503
            assert response.json()["detail"]["mode"] == "replay"


class TestCompletedRun:
    def test_full_run_returns_verified_result(self, client):
        job_id = start(client)
        body = wait_for(client, job_id)

        assert "status" not in body  # a finished run returns the result contract
        assert body["mode"] == "live"
        assert body["verification"]["verdict"] == "verified_fixed"
        assert body["verification"]["expectedTests"] == 6
        assert body["verification"]["reference"]["passed"] == 6
        assert body["astValidation"]["passed"] is True
        assert body["code"]["filename"] == "transactions.py"
        assert body["code"]["candidate"].startswith("# candidate repair")

    def test_refund_alias_surfaces_as_registry_id(self, client):
        job_id = start(client, "incorrect_refund")
        body = wait_for(client, job_id)
        assert body["scenarioId"] == "incorrect_refund"

    def test_precision_scenario_runs(self, client):
        job_id = start(client, "monetary_precision")
        body = wait_for(client, job_id)
        assert body["verification"]["expectedTests"] == 5
        assert body["financial"]["discrepancy"] == "4E-17"

    def test_workspace_is_cleaned_up(self, client, settings):
        job_id = start(client)
        wait_for(client, job_id)
        assert not (settings.workspace_root / job_id).exists()

    def test_concurrency_slot_released(self, client, settings):
        from api.limits import RateLimiter

        job_id = start(client)
        wait_for(client, job_id)
        limiter = RateLimiter(settings.state_dir / "limits.sqlite3", settings.limits)
        assert limiter.snapshot()["running"] == 0


class TestFailureModes:
    def test_partial_result_is_an_error(self, client, monkeypatch):
        monkeypatch.setenv("FAKE_MODE", "partial")
        job_id = start(client)
        body = wait_for(client, job_id)
        assert body["verification"]["verdict"] == "not_fixed"

    def test_crashing_child_is_reported_cleanly(self, client, monkeypatch):
        monkeypatch.setenv("FAKE_MODE", "crash")
        job_id = start(client)
        body = wait_for(client, job_id)
        assert body["status"] in {"error", "done"}
        assert "verification" not in body or body["verification"]["verdict"] != "verified_fixed"

    def test_timeout_kills_the_child(self, client, monkeypatch):
        monkeypatch.setenv("FAKE_MODE", "hang")
        client.app_ref.state.settings  # settings are frozen; override the manager's copy
        manager = client.app_ref.state.manager
        object.__setattr__(manager.settings, "child_timeout_seconds", 1)
        job_id = start(client)
        body = wait_for(client, job_id, timeout=20)
        assert body["status"] == "error"
        assert "exceeded" in json.dumps(body).lower() or body.get("message")


class TestArtifactsAndSecurity:
    def test_artifacts_are_whitelisted(self, client):
        job_id = start(client)
        wait_for(client, job_id)
        assert client.get(f"/api/investigations/{job_id}/artifacts/original.py").status_code == 200
        assert client.get(f"/api/investigations/{job_id}/artifacts/candidate.py").status_code == 200
        assert client.get(f"/api/investigations/{job_id}/artifacts/report.json").status_code == 200
        assert client.get(f"/api/investigations/{job_id}/artifacts/../../etc/passwd").status_code == 404
        assert client.get(f"/api/investigations/{job_id}/artifacts/workflow.py").status_code == 404

    def test_unknown_job_is_404(self, client):
        assert client.get("/api/investigations/" + "b" * 32).status_code == 404
        assert client.get("/api/investigations/not-a-valid-id").status_code == 404

    def test_no_credentials_in_any_response(self, client, monkeypatch):
        monkeypatch.setenv("FAKE_ECHO_SECRET", TEST_SECRET)
        job_id = start(client)
        body = wait_for(client, job_id)

        payloads = [
            json.dumps(client.get(f"/api/investigations/{job_id}").json()),
            json.dumps(client.get("/api/health").json()),
            client.get(f"/api/investigations/{job_id}/artifacts/report.json").text,
        ]
        for payload in payloads:
            assert TEST_SECRET not in payload

    def test_executable_log_echo_is_scrubbed(self, client, monkeypatch):
        monkeypatch.setenv("FAKE_ECHO_SECRET", TEST_SECRET)
        job_id = start(client)
        wait_for(client, job_id)
        logs = client.get(f"/api/investigations/{job_id}").json()["logs"]
        assert TEST_SECRET not in logs["reference"]
        assert "[REDACTED]" in logs["reference"]

    def test_docs_and_openapi_are_not_exposed(self, client):
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404


class TestRateLimiting:
    def test_second_concurrent_request_is_rejected(self, client, monkeypatch):
        monkeypatch.setenv("FAKE_MODE", "hang")
        manager = client.app_ref.state.manager
        object.__setattr__(manager.settings, "child_timeout_seconds", 5)

        first = client.post("/api/investigations", json={"scenario_id": "duplicate_transaction"})
        assert first.status_code == 202
        second = client.post("/api/investigations", json={"scenario_id": "duplicate_transaction"})
        assert second.status_code == 429
        assert second.json()["detail"]["error"] == "concurrent_limit"

        wait_for(client, first.json()["id"], timeout=20)

    def test_hourly_limit_after_completed_runs(self, client):
        first = start(client)
        wait_for(client, first)
        second = start(client)
        wait_for(client, second)
        third = client.post("/api/investigations", json={"scenario_id": "duplicate_transaction"})
        assert third.status_code == 429
        assert third.json()["detail"]["error"] == "per_ip_hour"
        assert third.json()["detail"]["mode"] == "replay"

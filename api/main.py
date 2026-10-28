"""FastAPI application.

Routes are thin: they validate input, consult the limiter, and hand off to the job
manager. Nothing here imports the backend's model clients, and no route can cause
arbitrary code to run — `scenario_id` is a closed enum of three fixed values.

Replay mode is never unavailable: if live runs are disabled, rate-limited, or the
adapter is down, the frontend keeps serving the recorded demonstrations.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from . import __version__
from .config import SCENARIOS, Settings
from .contracts import (
    HealthResponse,
    InvestigationResult,
    JobStatusResponse,
    LimitDecision,
    ScenarioSummary,
    StartRequest,
    StartResponse,
)
from .jobs import JobManager, valid_job_id
from .limits import RateLimiter
from .redact import SecretScrubber

# Artifacts a client may fetch. Fixed list — no user-supplied names reach the FS.
ALLOWED_ARTIFACTS = {"original.py", "candidate.py", "report.json"}

ARTIFACT_SOURCES = {
    "original.py": "source",
    "candidate.py": "candidate",
    "report.json": "report",
}


def create_app(settings: Settings | None = None, scrubber: SecretScrubber | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    scrubber = scrubber or SecretScrubber(settings.secret_values())

    state_dir = settings.state_dir
    state_dir.mkdir(parents=True, exist_ok=True)
    limiter = RateLimiter(state_dir / "limits.sqlite3", settings.limits)
    manager = JobManager(settings, limiter, scrubber)

    app = FastAPI(
        title="RootCause AI — API adapter",
        version=__version__,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,  # keep the surface small on a public deployment
    )
    app.state.settings = settings
    app.state.limiter = limiter
    app.state.manager = manager
    app.state.scrubber = scrubber

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["content-type"],
        max_age=600,
    )

    # ------------------------------------------------------------------ helpers

    def client_ip(request: Request) -> str:
        if settings.trust_proxy:
            forwarded = request.headers.get("x-forwarded-for", "")
            if forwarded:
                return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    @app.exception_handler(Exception)
    async def unhandled(_: Request, error: Exception) -> JSONResponse:  # pragma: no cover
        message = scrubber.scrub(f"{type(error).__name__}: {error}")
        return JSONResponse(status_code=500, content={"detail": message or "Internal error"})

    # ------------------------------------------------------------------- routes

    @app.get("/api/health", response_model=HealthResponse, response_model_by_alias=True)
    async def health() -> HealthResponse:
        snapshot = limiter.snapshot()
        return HealthResponse(
            ok=True,
            live_enabled=settings.live_enabled,
            mode="live" if settings.live_enabled else "replay",
            sandbox_ready=None,  # verified in M2, not claimed here
            queue={
                "running": snapshot["running"],
                "global_remaining_today": snapshot["global_remaining_today"],
            },
            limits={
                "per_ip_hour": snapshot["per_ip_hour"],
                "per_ip_day": snapshot["per_ip_day"],
                "global_day": snapshot["global_day"],
                "max_concurrent": snapshot["max_concurrent"],
            },
        )

    @app.get("/api/scenarios", response_model=list[ScenarioSummary], response_model_by_alias=True)
    async def scenarios() -> list[ScenarioSummary]:
        return [
            ScenarioSummary(
                id=scenario_id,  # type: ignore[arg-type]
                title=str(meta["title"]),
                tag=str(meta["tag"]),
                source_file=str(meta["source_file"]),
                test_file=str(meta["test_file"]),
                test_count=int(meta["test_count"]),  # type: ignore[arg-type]
                visual=str(meta["visual"]),
            )
            for scenario_id, meta in SCENARIOS.items()
        ]

    @app.post(
        "/api/investigations",
        response_model=StartResponse,
        response_model_by_alias=True,
        status_code=status.HTTP_202_ACCEPTED,
    )
    async def start_investigation(payload: StartRequest, request: Request) -> Any:
        ip = client_ip(request)

        if not settings.live_enabled:
            # Replay stays fully usable; this only says live execution is off.
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "live_disabled",
                    "message": "Live investigations are disabled. Recorded demonstrations remain available.",
                    "mode": "replay",
                },
            )

        if payload.scenario_id not in SCENARIOS:
            raise HTTPException(status_code=400, detail="Unknown scenario")

        manager.prune()
        job, reason = manager.start(payload.scenario_id, ip)

        if job is None:
            decision = LimitDecision(allowed=False, reason=reason)
            if reason in {"per_ip_hour", "per_ip_day", "global_day", "concurrent_limit"}:
                snapshot = limiter.snapshot()
                headers = {"Retry-After": "60"}
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": reason,
                        "message": "Demonstration limits reached. Recorded investigations remain available.",
                        "mode": "replay",
                        "limits": {
                            "per_ip_hour": snapshot["per_ip_hour"],
                            "per_ip_day": snapshot["per_ip_day"],
                            "global_day": snapshot["global_day"],
                        },
                    },
                    headers=headers,
                )
            raise HTTPException(status_code=400, detail=decision.reason)

        return StartResponse(id=job.id, status=job.status, position=0)

    @app.get("/api/investigations/{job_id}", response_model_by_alias=True)
    async def investigation(job_id: str) -> Any:
        if not valid_job_id(job_id):
            raise HTTPException(status_code=404, detail="Unknown investigation")
        job = manager.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Unknown investigation")

        if job.status == "done" and job.result is not None:
            return InvestigationResult(**job.result).model_dump(by_alias=True)
        if job.status == "error":
            return JobStatusResponse(
                id=job.id,
                status="error",
                scenario_id=job.scenario_id,  # type: ignore[arg-type]
                created_at=str(job.created_at),
                stage=job.stage,
                message=job.error or "The investigation failed.",
            ).model_dump(by_alias=True)
        return JobStatusResponse(
            id=job.id,
            status=job.status,  # type: ignore[arg-type]
            scenario_id=job.scenario_id,  # type: ignore[arg-type]
            created_at=str(job.created_at),
            stage=job.stage,
        ).model_dump(by_alias=True)

    @app.get("/api/investigations/{job_id}/events")
    async def events(job_id: str, request: Request) -> StreamingResponse:
        if not valid_job_id(job_id):
            raise HTTPException(status_code=404, detail="Unknown investigation")
        job = manager.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Unknown investigation")

        queue = job.subscribe()

        async def stream():
            try:
                while True:
                    if await request.is_disconnected():
                        break
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=15)
                    except asyncio.TimeoutError:
                        yield ": keepalive\n\n"
                        if job.status in {"done", "error"}:
                            break
                        continue
                    yield f"event: {event.get('type', 'message')}\ndata: {json.dumps(event)}\n\n"
                    if event.get("type") in {"result", "error"}:
                        break
            finally:
                job.unsubscribe(queue)

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/investigations/{job_id}/artifacts/{name}")
    async def artifact(job_id: str, name: str) -> Any:
        if not valid_job_id(job_id):
            raise HTTPException(status_code=404, detail="Not found")
        if name not in ALLOWED_ARTIFACTS:
            # Path traversal and arbitrary file reads are impossible by construction.
            raise HTTPException(status_code=404, detail="Not found")

        job = manager.get(job_id)
        if job is None or job.result is None:
            raise HTTPException(status_code=404, detail="Not found")

        kind = ARTIFACT_SOURCES[name]
        if kind == "source":
            body = job.result["code"]["original"]
        elif kind == "candidate":
            body = job.result["code"]["candidate"]
        else:
            body = json.dumps(job.result, indent=2)

        media = "application/json" if name.endswith(".json") else "text/plain; charset=utf-8"
        return StreamingResponse(iter([body]), media_type=media)

    return app


app = create_app()


def __getattr__(name: str) -> Any:  # pragma: no cover
    if name == "manager":
        return app.state.manager
    raise AttributeError(name)

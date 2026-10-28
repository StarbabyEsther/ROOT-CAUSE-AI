"""Runtime configuration for the adapter.

Every value comes from the environment so that secrets and limits live in the
platform's secret store, never in the repository. `Settings` is immutable and is
built once at application startup.

Secrets (`NEBIUS_API_KEY`, `NEBIUS_MODEL`, `CONTREE_PROJECT_ID`, `CONTREE_TOKEN`)
are intentionally *not* modelled here. They are read only to build a redactor and
are passed to the child process through the environment it inherits.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# Environment variable names the adapter understands.
ENV_LIVE_ENABLED = "LIVE_RUNS_ENABLED"
ENV_STATE_DIR = "RC_STATE_DIR"
ENV_WORKSPACE_ROOT = "RC_WORKSPACE_ROOT"
ENV_ALLOWED_ORIGINS = "RC_ALLOWED_ORIGINS"
ENV_CHILD_COMMAND = "RC_CHILD_COMMAND"
ENV_BACKEND_DIR = "RC_BACKEND_DIR"
ENV_TRUST_PROXY = "RC_TRUST_PROXY"

# Secrets scrubbed from anything that leaves the server.
SECRET_ENV_VARS = (
    "NEBIUS_API_KEY",
    "NEBIUS_MODEL",
    "CONTREE_TOKEN",
    "CONTREE_PROJECT_ID",
)

DEFAULT_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
)


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, default: int) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Limits:
    """Rate limits chosen for a public, no-login demo."""

    per_ip_hour: int = 2
    per_ip_day: int = 5
    global_day: int = 30
    max_concurrent: int = 1


@dataclass(frozen=True)
class Settings:
    # Live runs are OFF unless explicitly enabled. Replay stays available either way.
    live_enabled: bool = False

    limits: Limits = field(default_factory=Limits)

    # Where the SQLite limiter lives. Must be a persistent volume in production so
    # that limits survive restarts and redeploys.
    state_dir: Path = Path("/tmp/rcai-state")
    workspace_root: Path = Path("/tmp/rcai-work")

    # Directory holding the unmodified backend modules to copy into each job.
    backend_dir: Path = Path(__file__).resolve().parent.parent

    allowed_origins: tuple[str, ...] = DEFAULT_ORIGINS

    # Hard ceilings. The workflow itself allows 600 s; we stop it slightly later so
    # the child can finish writing its report, but never let a job hang forever.
    child_timeout_seconds: int = 660
    job_ttl_seconds: int = 3600
    max_log_bytes: int = 256_000

    # Only honour X-Forwarded-For behind a trusted proxy (Fly.io sets it).
    trust_proxy: bool = False

    # Test seam: when set, the adapter runs this command instead of the real
    # backend entry point. Never used in production.
    child_command: tuple[str, ...] | None = None

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "Settings":
        env = dict(os.environ if env is None else env)

        origins_raw = env.get(ENV_ALLOWED_ORIGINS, "")
        origins = (
            tuple(o.strip() for o in origins_raw.split(",") if o.strip())
            if origins_raw.strip()
            else DEFAULT_ORIGINS
        )

        child_raw = env.get(ENV_CHILD_COMMAND, "").strip()
        child_command = tuple(child_raw.split()) if child_raw else None

        return cls(
            live_enabled=_as_bool(env.get(ENV_LIVE_ENABLED), False),
            limits=Limits(
                per_ip_hour=_as_int(env.get("RC_PER_IP_HOUR"), 2),
                per_ip_day=_as_int(env.get("RC_PER_IP_DAY"), 5),
                global_day=_as_int(env.get("RC_GLOBAL_DAY"), 30),
                max_concurrent=_as_int(env.get("RC_MAX_CONCURRENT"), 1),
            ),
            state_dir=Path(env.get(ENV_STATE_DIR, "/tmp/rcai-state")),
            workspace_root=Path(env.get(ENV_WORKSPACE_ROOT, "/tmp/rcai-work")),
            backend_dir=Path(env.get(ENV_BACKEND_DIR, str(Path(__file__).resolve().parent.parent))),
            allowed_origins=origins,
            trust_proxy=_as_bool(env.get(ENV_TRUST_PROXY), False),
            child_command=child_command,
        )

    def secret_values(self, env: dict[str, str] | None = None) -> list[str]:
        """Secret strings to scrub from logs. Never logged themselves."""
        env = dict(os.environ if env is None else env)
        values = [env.get(name, "") for name in SECRET_ENV_VARS]
        return [v for v in values if len(v) >= 8]


# Scenario registry mirrored from `scenario_registry.py` + `workflow.py`.
# Kept here so the adapter never imports the backend into the server process.
SCENARIOS: dict[str, dict[str, object]] = {
    "duplicate_transaction": {
        "title": "Duplicate transactions",
        "tag": "Transaction integrity",
        "source_file": "transactions.py",
        "test_file": "test_financial_regression.py",
        "test_count": 6,
        "visual": "duplicate",
    },
    "incorrect_refund": {
        "title": "Incorrect refunds",
        "tag": "Refund reconciliation",
        "source_file": "refund_processor.py",
        "test_file": "test_refund_processor.py",
        "test_count": 7,
        "visual": "sign",
    },
    "monetary_precision": {
        "title": "Monetary precision",
        "tag": "Numerical accuracy",
        "source_file": "precision_processor.py",
        "test_file": "test_precision_processor.py",
        "test_count": 5,
        "visual": "precision",
    },
}

# Raw scenario ids the backend writes into its own reports.
SCENARIO_ID_ALIASES = {
    "refund_sign_error": "incorrect_refund",
    "duplicate_transaction": "duplicate_transaction",
    "monetary_precision": "monetary_precision",
}

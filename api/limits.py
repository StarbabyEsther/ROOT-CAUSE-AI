"""Persistent rate limiting and the global concurrency gate.

Why SQLite: the limits must survive process restarts *and* redeploys, which rules
out in-memory counters. A single SQLite file in `RC_STATE_DIR` gives us durable
counters, and `BEGIN IMMEDIATE` gives us an atomic read-modify-write so that
simultaneous requests cannot each pass the same check — including the "only one
investigation at a time" rule.

Single-writer assumption: the database serialises writers, so this is correct for
one API machine. If the API is ever scaled horizontally, the limiter must move to
a shared store (see README) — the interface is deliberately narrow to make that
swap local.
"""

from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .config import Limits

HOUR = 3600
DAY = 86400

_SCHEMA = """
CREATE TABLE IF NOT EXISTS hits (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ip      TEXT    NOT NULL,
    ts      REAL    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_hits_ip_ts ON hits(ip, ts);
CREATE INDEX IF NOT EXISTS idx_hits_ts    ON hits(ts);

CREATE TABLE IF NOT EXISTS active (
    job_id   TEXT PRIMARY KEY,
    ip       TEXT NOT NULL,
    started  REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_active_started ON active(started);
"""


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str
    retry_after_seconds: int = 0
    remaining_hour: int = 0
    remaining_day: int = 0
    remaining_global: int = 0


class RateLimiter:
    """Durable per-IP and global limits plus a concurrency gate."""

    def __init__(self, db_path: Path | str, limits: Limits, stale_after: int = 900) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.limits = limits
        self.stale_after = stale_after
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(str(self.db_path), timeout=10.0, isolation_level=None)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA busy_timeout=10000")
            yield conn
        finally:
            conn.close()

    # ------------------------------------------------------------------ public

    def check_and_claim(self, ip: str, job_id: str) -> Decision:
        """Atomically test every limit and, if all pass, record the attempt.

        Recording and testing happen inside one IMMEDIATE transaction, so N
        concurrent callers cannot all observe "under the cap".
        """
        now = time.time()
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                self._release_stale(conn, now)

                running = conn.execute("SELECT COUNT(*) FROM active").fetchone()[0]
                used_hour = conn.execute(
                    "SELECT COUNT(*) FROM hits WHERE ip = ? AND ts > ?", (ip, now - HOUR)
                ).fetchone()[0]
                used_day = conn.execute(
                    "SELECT COUNT(*) FROM hits WHERE ip = ? AND ts > ?", (ip, now - DAY)
                ).fetchone()[0]
                used_global = conn.execute(
                    "SELECT COUNT(*) FROM hits WHERE ts > ?", (now - DAY,)
                ).fetchone()[0]

                remaining_hour = max(0, self.limits.per_ip_hour - used_hour)
                remaining_day = max(0, self.limits.per_ip_day - used_day)
                remaining_global = max(0, self.limits.global_day - used_global)

                if running >= self.limits.max_concurrent:
                    conn.execute("COMMIT")
                    return Decision(
                        allowed=False,
                        reason="concurrent_limit",
                        retry_after_seconds=30,
                        remaining_hour=remaining_hour,
                        remaining_day=remaining_day,
                        remaining_global=remaining_global,
                    )

                if used_hour >= self.limits.per_ip_hour:
                    conn.execute("COMMIT")
                    return Decision(
                        allowed=False,
                        reason="per_ip_hour",
                        retry_after_seconds=self._seconds_until_hourly_slot(conn, ip, now),
                        remaining_hour=remaining_hour,
                        remaining_day=remaining_day,
                        remaining_global=remaining_global,
                    )

                if used_day >= self.limits.per_ip_day:
                    conn.execute("COMMIT")
                    return Decision(
                        allowed=False,
                        reason="per_ip_day",
                        retry_after_seconds=self._seconds_until_daily_slot(conn, ip, now),
                        remaining_hour=remaining_hour,
                        remaining_day=remaining_day,
                        remaining_global=remaining_global,
                    )

                if used_global >= self.limits.global_day:
                    conn.execute("COMMIT")
                    return Decision(
                        allowed=False,
                        reason="global_day",
                        retry_after_seconds=DAY,
                        remaining_hour=remaining_hour,
                        remaining_day=remaining_day,
                        remaining_global=remaining_global,
                    )

                conn.execute("INSERT INTO hits (ip, ts) VALUES (?, ?)", (ip, now))
                conn.execute(
                    "INSERT OR REPLACE INTO active (job_id, ip, started) VALUES (?, ?, ?)",
                    (job_id, ip, now),
                )
                conn.execute("COMMIT")
                return Decision(
                    allowed=True,
                    reason="allowed",
                    remaining_hour=remaining_hour - 1,
                    remaining_day=remaining_day - 1,
                    remaining_global=remaining_global - 1,
                )
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def release(self, job_id: str) -> None:
        """Free the concurrency slot. Safe to call twice."""
        with self._connect() as conn:
            conn.execute("DELETE FROM active WHERE job_id = ?", (job_id,))

    def snapshot(self) -> dict[str, int]:
        now = time.time()
        with self._connect() as conn:
            self._release_stale(conn, now)
            running = conn.execute("SELECT COUNT(*) FROM active").fetchone()[0]
            used_global = conn.execute("SELECT COUNT(*) FROM hits WHERE ts > ?", (now - DAY,)).fetchone()[0]
        return {
            "running": running,
            "global_used_today": used_global,
            "global_remaining_today": max(0, self.limits.global_day - used_global),
            "per_ip_hour": self.limits.per_ip_hour,
            "per_ip_day": self.limits.per_ip_day,
            "global_day": self.limits.global_day,
            "max_concurrent": self.limits.max_concurrent,
        }

    # ----------------------------------------------------------------- private

    def _release_stale(self, conn: sqlite3.Connection, now: float) -> None:
        """A crashed or killed job must not block the demo forever."""
        conn.execute("DELETE FROM active WHERE started < ?", (now - self.stale_after,))

    def _seconds_until_hourly_slot(self, conn: sqlite3.Connection, ip: str, now: float) -> int:
        row = conn.execute(
            "SELECT MIN(ts) FROM (SELECT ts FROM hits WHERE ip = ? AND ts > ? ORDER BY ts DESC LIMIT ?)",
            (ip, now - HOUR, self.limits.per_ip_hour),
        ).fetchone()
        oldest = row[0] if row else None
        return max(1, int((oldest or now) + HOUR - now)) if oldest else HOUR

    def _seconds_until_daily_slot(self, conn: sqlite3.Connection, ip: str, now: float) -> int:
        row = conn.execute(
            "SELECT MIN(ts) FROM (SELECT ts FROM hits WHERE ip = ? AND ts > ? ORDER BY ts DESC LIMIT ?)",
            (ip, now - DAY, self.limits.per_ip_day),
        ).fetchone()
        oldest = row[0] if row else None
        return max(1, int((oldest or now) + DAY - now)) if oldest else DAY

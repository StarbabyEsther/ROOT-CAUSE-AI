"""Persistent limits: per-IP, global, concurrency, restart survival."""

from __future__ import annotations

import threading
import time

from api.config import Limits
from api.limits import RateLimiter


def make(tmp_path, **overrides):
    limits = Limits(
        per_ip_hour=overrides.get("per_ip_hour", 2),
        per_ip_day=overrides.get("per_ip_day", 5),
        global_day=overrides.get("global_day", 30),
        max_concurrent=overrides.get("max_concurrent", 1),
    )
    return RateLimiter(tmp_path / "limits.sqlite3", limits)


def test_hourly_limit_enforced(tmp_path):
    limiter = make(tmp_path, per_ip_hour=2)
    assert limiter.check_and_claim("1.2.3.4", "j1").allowed
    limiter.release("j1")
    assert limiter.check_and_claim("1.2.3.4", "j2").allowed
    limiter.release("j2")
    third = limiter.check_and_claim("1.2.3.4", "j3")
    assert not third.allowed
    assert third.reason == "per_ip_hour"


def test_daily_limit_enforced(tmp_path):
    limiter = make(tmp_path, per_ip_hour=10, per_ip_day=3)
    for index in range(3):
        assert limiter.check_and_claim("1.2.3.4", f"j{index}").allowed
        limiter.release(f"j{index}")
    decision = limiter.check_and_claim("1.2.3.4", "j3")
    assert not decision.allowed
    assert decision.reason == "per_ip_day"


def test_global_limit_reached(tmp_path):
    limiter = make(tmp_path, per_ip_hour=10, per_ip_day=10, global_day=3)
    for index in range(3):
        ip = f"10.0.0.{index}"
        assert limiter.check_and_claim(ip, f"j{index}").allowed
        limiter.release(f"j{index}")
    decision = limiter.check_and_claim("10.0.0.99", "j9")
    assert not decision.allowed
    assert decision.reason == "global_day"


def test_concurrency_gate(tmp_path):
    limiter = make(tmp_path, max_concurrent=1)
    assert limiter.check_and_claim("1.1.1.1", "j1").allowed
    second = limiter.check_and_claim("2.2.2.2", "j2")
    assert not second.allowed
    assert second.reason == "concurrent_limit"
    limiter.release("j1")
    assert limiter.check_and_claim("2.2.2.2", "j3").allowed


def test_limits_survive_restart(tmp_path):
    first = make(tmp_path, per_ip_hour=2)
    assert first.check_and_claim("1.2.3.4", "j1").allowed
    first.release("j1")

    # New process, same state directory — the counter must persist.
    second = make(tmp_path, per_ip_hour=2)
    assert second.check_and_claim("1.2.3.4", "j2").allowed
    second.release("j2")
    assert not second.check_and_claim("1.2.3.4", "j3").allowed


def test_stale_slots_are_reclaimed(tmp_path):
    limiter = RateLimiter(tmp_path / "limits.sqlite3", Limits(), stale_after=1)
    assert limiter.check_and_claim("1.2.3.4", "j1").allowed
    time.sleep(1.2)
    # A crashed job must not block the demo forever.
    assert limiter.check_and_claim("5.6.7.8", "j2").allowed


def test_concurrent_callers_cannot_exceed_global_cap(tmp_path):
    """The headline guarantee: parallel requests cannot each pass the same check."""
    limiter = make(tmp_path, per_ip_hour=100, per_ip_day=100, global_day=5, max_concurrent=100)
    granted: list[str] = []
    lock = threading.Lock()

    def attempt(index: int) -> None:
        decision = limiter.check_and_claim(f"9.9.9.{index % 30}", f"job{index}")
        if decision.allowed:
            with lock:
                granted.append(f"job{index}")

    threads = [threading.Thread(target=attempt, args=(i,)) for i in range(30)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(granted) == 5, f"granted {len(granted)} runs, cap is 5"


def test_snapshot_reports_remaining(tmp_path):
    limiter = make(tmp_path, per_ip_hour=2, global_day=30)
    limiter.check_and_claim("1.2.3.4", "j1")
    snapshot = limiter.snapshot()
    assert snapshot["running"] == 1
    assert snapshot["global_used_today"] == 1
    assert snapshot["global_remaining_today"] == 29

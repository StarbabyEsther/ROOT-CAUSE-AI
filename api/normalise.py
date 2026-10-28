"""Turn inconsistent backend artifacts into the client contract.

The three repair paths in this repository do not agree on their report shape:

    duplicate  → scenario_id "duplicate_transaction", has baseline_passed, elapsed_seconds
    refund     → scenario_id "refund_sign_error",     no elapsed_seconds, no baseline_passed
    precision  → scenario_id "monetary_precision",    no elapsed_seconds, no baseline_passed

Normalising here means the frontend never sees that variation, and a report that
is merely *present* is never presented as a verified repair: `verified_fixed` is
only emitted when the backend said so **and** the test counts agree with the
scenario's protected suite.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from .config import SCENARIO_ID_ALIASES, SCENARIOS
from .contracts import (
    AstValidation,
    CodeArtifact,
    Diagnosis,
    FinancialReport,
    InvestigationResult,
    Logs,
    NegativeControl,
    PatchProposal,
    Provenance,
    ReferenceCounts,
    RunCounts,
    TestCaseResult,
    VerificationReport,
)

SANDBOX_LABEL = "Nebius sandbox via contree (disposable) — 2 executions per run"

# unittest verbose rows: "test_name (module.Class.test_name) ... ok"
_TEST_LINE = re.compile(
    r"^(?P<name>\w+) \((?P<suite>[\w.]+)\) \.\.\. (?P<status>ok|FAIL|ERROR|skipped[^)]*)\s*$",
    re.MULTILINE,
)
_RAN = re.compile(r"^Ran (\d+) tests?", re.MULTILINE)
_FAILURES = re.compile(r"failures=(\d+)")
_ERRORS = re.compile(r"errors=(\d+)")


def normalise_scenario_id(raw: str | None, fallback: str) -> str:
    """Map a report's own id onto the registry id."""
    if not raw:
        return fallback
    return SCENARIO_ID_ALIASES.get(raw, fallback)


def parse_unittest_output(text: str) -> dict[str, Any]:
    """Extract counts and per-test outcomes from verbose unittest output."""
    tests: list[dict[str, str]] = []
    for match in _TEST_LINE.finditer(text or ""):
        status = match.group("status")
        suite_parts = match.group("suite").split(".")
        tests.append(
            {
                "name": match.group("name"),
                "suite": suite_parts[-2] if len(suite_parts) > 1 else match.group("suite"),
                "state": "pass" if status.startswith("ok") else "skip" if status.startswith("skipped") else "fail",
            }
        )

    ran_match = _RAN.search(text or "")
    ran = int(ran_match.group(1)) if ran_match else len(tests)
    failures = int(m.group(1)) if (m := _FAILURES.search(text or "")) else 0
    errors = int(m.group(1)) if (m := _ERRORS.search(text or "")) else 0
    return {
        "ran": ran,
        "failed": failures + errors,
        "tests": tests,
    }


def _tail(text: str, limit: int) -> str:
    if not text:
        return ""
    return text if len(text) <= limit else "…\n" + text[-limit:]


def _to_test_state(value: str) -> str:
    return "pass" if value == "pass" else "skip" if value == "skip" else "fail"


def build_result(
    *,
    job_id: str,
    scenario_id: str,
    financial: dict[str, Any],
    workflow: dict[str, Any],
    patch: dict[str, Any] | None,
    ast: dict[str, Any] | None,
    original_source: str,
    candidate_source: str,
    baseline_logs: str,
    child_logs: str = "",
    max_log_bytes: int = 256_000,
) -> InvestigationResult:
    """Assemble a validated `InvestigationResult`.

    Every value is either taken from the backend's own output or computed from
    its logs. Nothing is invented: a missing report yields an `error` verdict,
    not a passing one.
    """
    meta = SCENARIOS[scenario_id]
    expected_tests = int(meta["test_count"])
    source_file = str(meta["source_file"])

    raw_verification: dict[str, Any] = workflow.get("verification") or {}
    sandbox_logs = str(raw_verification.get("logs") or "")
    backend_logs = str(workflow.get("logs") or "")
    combined = "\n".join(part for part in (sandbox_logs, backend_logs, child_logs) if part)

    # --- verdict: only trust it when the test counts actually line up --------
    reported_verdict = raw_verification.get("verdict")
    final_passed = raw_verification.get("final_passed")
    final_failed = raw_verification.get("final_failed")

    counts_agree = (
        isinstance(final_passed, int)
        and isinstance(final_failed, int)
        and final_passed + final_failed == expected_tests
        and final_failed == 0
    )

    if not raw_verification or reported_verdict is None:
        verdict = "error"
    elif reported_verdict == "verified_fixed" and counts_agree:
        verdict = "verified_fixed"
    elif reported_verdict == "verified_fixed":
        # Backend claimed success but the protected suite does not add up.
        verdict = "error"
    elif reported_verdict in {"not_fixed", "error"}:
        verdict = reported_verdict
    else:
        verdict = "error"

    # --- per-test matrix -----------------------------------------------------
    candidate_parsed = parse_unittest_output(sandbox_logs or backend_logs)
    baseline_parsed = parse_unittest_output(baseline_logs)

    baseline_state = {t["name"]: t["state"] for t in baseline_parsed["tests"]}
    candidate_state = {t["name"]: t["state"] for t in candidate_parsed["tests"]}

    if candidate_state:
        names = list(candidate_state)
    elif baseline_state:
        names = list(baseline_state)
    else:
        names = []

    tests = [
        TestCaseResult(
            name=name,
            suite=_suite_for(name, baseline_parsed, candidate_parsed),
            baseline=_to_test_state(baseline_state.get(name, "fail" if name else "skip")),
            reference=_to_test_state(candidate_state.get(name, "skip")),
        )
        for name in names
    ]

    baseline_ran = baseline_parsed["ran"] or expected_tests
    baseline_failed = baseline_parsed["failed"]
    if not baseline_parsed["tests"]:
        # Baseline could not be measured: report zeros rather than a fake figure.
        baseline_ran = 0
        baseline_failed = 0

    reference_passed = (
        final_passed if isinstance(final_passed, int) else candidate_parsed["ran"] - candidate_parsed["failed"]
    )
    reference_failed = final_failed if isinstance(final_failed, int) else candidate_parsed["failed"]

    verification = VerificationReport(
        scenario_id=scenario_id,  # type: ignore[arg-type]
        verdict=verdict,  # type: ignore[arg-type]
        expected_tests=expected_tests,
        baseline=RunCounts(ran=baseline_ran, failed=baseline_failed),
        reference=ReferenceCounts(
            ran=reference_passed + reference_failed,
            failed=reference_failed,
            passed=max(0, reference_passed),
        ),
        attempts=raw_verification.get("attempts") if isinstance(raw_verification.get("attempts"), int) else None,
        elapsed_seconds=(
            float(raw_verification["elapsed_seconds"])
            if isinstance(raw_verification.get("elapsed_seconds"), (int, float))
            else None
        ),
        sandbox=SANDBOX_LABEL,
        tests=tests,
    )

    proposal = PatchProposal(
        root_cause=str((patch or {}).get("root_cause") or ""),
        explanation=str((patch or {}).get("explanation") or ""),
        target_file=str((patch or {}).get("target_file") or source_file),
        proposed_code=str((patch or {}).get("proposed_code") or ""),
    )

    ast_payload = ast or {}
    ast_validation = AstValidation(
        passed=bool(ast_payload.get("passed")),
        reason=str(ast_payload.get("reason") or "Structural validation result unavailable."),
        negative_control=NegativeControl(
            passed=bool((ast_payload.get("negativeControl") or {}).get("passed", False)),
            reason=str((ast_payload.get("negativeControl") or {}).get("reason") or "not evaluated"),
        ),
    )

    return InvestigationResult(
        id=job_id,
        scenario_id=scenario_id,  # type: ignore[arg-type]
        mode="live",
        financial=FinancialReport(**financial),
        diagnosis=Diagnosis(
            root_cause=proposal.root_cause or "The run produced no diagnosis.",
            explanation=proposal.explanation or "",
            illustrative=False,
        ),
        reference=proposal,
        verification=verification,
        code=CodeArtifact(
            filename=source_file,
            original=original_source,
            candidate=candidate_source or proposal.proposed_code,
        ),
        ast_validation=ast_validation,
        logs=Logs(
            baseline=_tail(baseline_logs, max_log_bytes),
            reference=_tail(combined, max_log_bytes),
        ),
        provenance=Provenance(
            financial="financial_investigator.investigate_transactions() executed in an isolated job workspace.",
            tests="Protected regression suite executed inside a disposable Nebius sandbox; baseline measured locally in the job workspace.",
            code="Source file copied from the repository; candidate taken from the generated patch artifact.",
            diagnosis="NVIDIA Nemotron via Nebius Token Factory, structured JSON response.",
            captured_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        ),
    )


def _suite_for(name: str, baseline: dict[str, Any], candidate: dict[str, Any]) -> str:
    for parsed in (candidate, baseline):
        for test in parsed.get("tests", []):
            if test["name"] == name:
                return str(test["suite"])
    return "unknown"

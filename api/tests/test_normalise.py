"""Normalisation of the three disagreeing backend report shapes."""

from __future__ import annotations

import pytest

from api.normalise import build_result, normalise_scenario_id, parse_unittest_output

FINANCIAL = {
    "issue_detected": True,
    "issue_type": "Possible duplicate processing",
    "duplicate_ids": ["TXN002"],
    "affected_transactions": ["TXN002"],
    "actual_total": "600.0",
    "expected_total": "400.00",
    "discrepancy": "200.00",
}

VERBOSE_OK = """test_a (m.Tests.test_a) ... ok
test_b (m.Tests.test_b) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.001s

OK
"""

VERBOSE_FAIL = """test_a (m.Tests.test_a) ... ok
test_b (m.Tests.test_b) ... FAIL

======================================================================
FAIL: test_b (m.Tests.test_b)
----------------------------------------------------------------------
Ran 2 tests in 0.001s

FAILED (failures=1)
"""


class TestScenarioId:
    def test_refund_alias_is_mapped(self):
        # The refund report writes "refund_sign_error"; the registry id differs.
        assert normalise_scenario_id("refund_sign_error", "incorrect_refund") == "incorrect_refund"

    def test_known_id_passes_through(self):
        assert normalise_scenario_id("monetary_precision", "monetary_precision") == "monetary_precision"

    def test_missing_id_falls_back(self):
        assert normalise_scenario_id(None, "duplicate_transaction") == "duplicate_transaction"


class TestParseOutput:
    def test_counts_and_states(self):
        parsed = parse_unittest_output(VERBOSE_FAIL)
        assert parsed["ran"] == 2
        assert parsed["failed"] == 1
        states = {t["name"]: t["state"] for t in parsed["tests"]}
        assert states == {"test_a": "pass", "test_b": "fail"}

    def test_ok_run(self):
        parsed = parse_unittest_output(VERBOSE_OK)
        assert parsed["failed"] == 0
        assert len(parsed["tests"]) == 2

    def test_empty_input_is_safe(self):
        assert parse_unittest_output("") == {"ran": 0, "failed": 0, "tests": []}


def _build(**overrides):
    base = dict(
        job_id="a" * 32,
        scenario_id="duplicate_transaction",
        financial=FINANCIAL,
        workflow={
            "verification": {
                "verdict": "verified_fixed",
                "final_passed": 6,
                "final_failed": 0,
                "attempts": 1,
            },
            "patch": {"root_cause": "r", "explanation": "e", "target_file": "transactions.py", "proposed_code": "x"},
            "logs": VERBOSE_OK,
        },
        patch={"root_cause": "r", "explanation": "e", "target_file": "transactions.py", "proposed_code": "x"},
        ast={"passed": True, "reason": "ok", "negativeControl": {"passed": False, "reason": "rejected"}},
        original_source="def calculate_total(t):\n    return 0\n",
        candidate_source="def calculate_total(t):\n    return 42\n",
        baseline_logs=VERBOSE_FAIL,
    )
    base.update(overrides)
    return build_result(**base)


class TestBuildResult:
    def test_verified_when_counts_agree(self):
        result = _build()
        assert result.verification.verdict == "verified_fixed"
        assert result.mode == "live"
        assert result.diagnosis.illustrative is False

    def test_mismatched_counts_are_downgraded(self):
        """A backend that claims success without the full suite must not look verified."""
        result = _build(
            workflow={
                "verification": {"verdict": "verified_fixed", "final_passed": 5, "final_failed": 0},
                "logs": VERBOSE_OK,
            }
        )
        assert result.verification.verdict == "error"

    def test_failed_tests_are_not_verified(self):
        result = _build(
            workflow={
                "verification": {"verdict": "verified_fixed", "final_passed": 5, "final_failed": 1},
                "logs": VERBOSE_FAIL,
            }
        )
        assert result.verification.verdict == "error"

    def test_missing_report_is_error_not_success(self):
        result = _build(workflow={"logs": ""})
        assert result.verification.verdict == "error"

    def test_refund_scenario_without_elapsed_or_baseline(self):
        """The refund report has neither elapsed_seconds nor baseline_passed."""
        result = _build(
            scenario_id="incorrect_refund",
            workflow={
                "verification": {"verdict": "verified_fixed", "final_passed": 7, "final_failed": 0},
                "logs": VERBOSE_OK,
            },
        )
        assert result.verification.verdict == "verified_fixed"
        assert result.verification.attempts is None
        assert result.verification.elapsed_seconds is None  # not fabricated as 0

    def test_baseline_matrix_uses_measured_output(self):
        result = _build()
        states = {t.name: (t.baseline, t.reference) for t in result.verification.tests}
        assert states["test_b"] == ("fail", "pass")

    def test_ast_result_is_carried_through(self):
        result = _build()
        assert result.ast_validation.passed is True
        assert result.ast_validation.negative_control.passed is False

    def test_serialises_to_camel_case(self):
        payload = _build().model_dump(by_alias=True)
        assert "scenarioId" in payload
        assert payload["verification"]["expectedTests"] == 6
        assert payload["verification"]["baseline"] == {"ran": 2, "failed": 1}
        # financial block stays snake_case: it is a verbatim backend passthrough
        assert payload["financial"]["issue_type"] == "Possible duplicate processing"

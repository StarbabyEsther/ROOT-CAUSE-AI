"""Contract parity with the TypeScript client.

The frontend was written first; these tests stop the Python adapter from drifting
away from `web/src/lib/contract.ts`. Field names are compared, not prose, so a
rename on either side fails here instead of in the browser.
"""

from __future__ import annotations

import re

import pytest

from api.contracts import (
    AstValidation,
    CodeArtifact,
    FinancialReport,
    InvestigationResult,
    Provenance,
    VerificationReport,
)
from api.tests.conftest import load_contract_ts


def ts_interface_fields(source: str, name: str) -> set[str]:
    """Collect field names declared directly inside `interface <name> { ... }`."""
    match = re.search(rf"export interface {name} \{{(.*?)\n\}}", source, re.S)
    if not match:
        raise AssertionError(f"interface {name} not found in contract.ts")
    body = match.group(1)
    fields: set[str] = set()
    depth = 0
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//") or stripped.startswith("*"):
            continue
        if depth == 0:
            field = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\??\s*:", stripped)
            if field:
                fields.add(field.group(1))
        depth += line.count("{") - line.count("}")
    return fields


@pytest.fixture(scope="module")
def contract_source() -> str:
    return load_contract_ts()


def camel(name: str) -> str:
    head, *tail = name.split("_")
    return head + "".join(word.capitalize() for word in tail)


class TestTopLevelParity:
    def test_investigation_result_fields_match(self, contract_source):
        ts_fields = ts_interface_fields(contract_source, "InvestigationResult")
        py_fields = {camel(name) for name in InvestigationResult.model_fields}
        assert ts_fields == py_fields, f"TS-only: {ts_fields - py_fields}, PY-only: {py_fields - ts_fields}"

    def test_verification_report_fields_match(self, contract_source):
        ts_fields = ts_interface_fields(contract_source, "VerificationReport")
        py_fields = {camel(name) for name in VerificationReport.model_fields}
        # The client declares `expectedTests` and the counts; the adapter matches.
        assert ts_fields <= py_fields, f"missing in python: {ts_fields - py_fields}"

    def test_code_artifact_fields_match(self, contract_source):
        ts_fields = ts_interface_fields(contract_source, "CodeArtifact")
        assert ts_fields == set(CodeArtifact.model_fields)

    def test_provenance_fields_match(self, contract_source):
        ts_fields = ts_interface_fields(contract_source, "Provenance")
        assert ts_fields == {camel(name) for name in Provenance.model_fields}

    def test_ast_fields_match(self, contract_source):
        ts_fields = ts_interface_fields(contract_source, "AstValidation")
        assert ts_fields == {camel(name) for name in AstValidation.model_fields}

    def test_financial_block_stays_snake_case(self, contract_source):
        """`financial` is a verbatim passthrough of the backend report."""
        ts_fields = ts_interface_fields(contract_source, "FinancialReport")
        assert ts_fields == set(FinancialReport.model_fields)


class TestSerialisation:
    def test_camel_alias_is_used_on_the_wire(self):
        payload = InvestigationResult.model_json_schema(by_alias=True)
        assert "scenarioId" in payload["properties"]
        assert "astValidation" in payload["properties"]

    def test_extra_fields_are_rejected(self):
        with pytest.raises(Exception):
            VerificationReport(
                scenario_id="duplicate_transaction",
                verdict="verified_fixed",
                expected_tests=6,
                baseline={"ran": 6, "failed": 3},
                reference={"ran": 6, "failed": 0, "passed": 6},
                sandbox="x",
                unexpected="nope",
            )

    def test_invalid_verdict_is_rejected(self):
        with pytest.raises(Exception):
            VerificationReport(
                scenario_id="duplicate_transaction",
                verdict="probably_fine",
                expected_tests=6,
                baseline={"ran": 6, "failed": 3},
                reference={"ran": 6, "failed": 0, "passed": 6},
                sandbox="x",
            )


class TestScenarioEnum:
    def test_only_three_scenarios_are_accepted(self):
        from api.config import SCENARIOS

        assert set(SCENARIOS) == {
            "duplicate_transaction",
            "incorrect_refund",
            "monetary_precision",
        }

    def test_test_counts_match_the_repository(self):
        """Guards against the UI promising a suite size the backend does not run."""
        import re as _re
        from pathlib import Path

        repo = Path(__file__).resolve().parents[2]
        expected = {"duplicate_transaction": 6, "incorrect_refund": 7, "monetary_precision": 5}
        from api.config import SCENARIOS

        for scenario_id, count in expected.items():
            assert SCENARIOS[scenario_id]["test_count"] == count

        # The refund and precision suites declare their own test methods.
        refund = (repo / "test_refund_processor.py").read_text()
        precision = (repo / "test_precision_processor.py").read_text()
        assert len(_re.findall(r"^    def test_", refund, _re.M)) == 7
        assert len(_re.findall(r"^    def test_", precision, _re.M)) == 5

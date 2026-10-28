"""Wire contract for the frontend.

These models are the single source of truth for what `/api/investigations/{id}`
returns. They mirror `web/src/lib/contract.ts` exactly — the TypeScript interfaces
are the client half of the same contract, and `tests/test_contract.py` asserts the
two stay in step.

Field naming follows the client: camelCase on the envelope, snake_case inside the
`financial` block because that block is a verbatim passthrough of what
`financial_investigator.py` emits.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def _camel(name: str) -> str:
    head, *tail = name.split("_")
    return head + "".join(word.capitalize() for word in tail)


class CamelModel(BaseModel):
    """Serialises snake_case attributes to the camelCase the client expects."""

    model_config = ConfigDict(
        alias_generator=_camel,
        populate_by_name=True,
        extra="forbid",
    )


ScenarioId = Literal["duplicate_transaction", "incorrect_refund", "monetary_precision"]
Verdict = Literal["verified_fixed", "not_fixed", "error"]
TestState = Literal["pass", "fail", "skip"]


class FinancialReport(BaseModel):
    """Verbatim shape of `investigate_transactions()` output."""

    model_config = ConfigDict(extra="forbid")

    issue_detected: bool
    issue_type: str
    duplicate_ids: list[str]
    affected_transactions: list[str]
    actual_total: str
    expected_total: str
    discrepancy: str


class PatchProposal(CamelModel):
    root_cause: str
    explanation: str
    target_file: str
    proposed_code: str


class TestCaseResult(CamelModel):
    name: str
    suite: str
    baseline: TestState
    reference: TestState


class RunCounts(CamelModel):
    ran: int = 0
    failed: int = 0


class ReferenceCounts(CamelModel):
    ran: int = 0
    failed: int = 0
    passed: int = 0


class VerificationReport(CamelModel):
    scenario_id: ScenarioId
    verdict: Verdict
    expected_tests: int
    baseline: RunCounts
    reference: ReferenceCounts
    attempts: int | None = None
    elapsed_seconds: float | None = None
    sandbox: str
    tests: list[TestCaseResult] = Field(default_factory=list)


class AstValidation(CamelModel):
    passed: bool
    reason: str
    negative_control: "NegativeControl"


class NegativeControl(CamelModel):
    passed: bool
    reason: str


class CodeArtifact(CamelModel):
    filename: str
    language: Literal["python"] = "python"
    original: str
    candidate: str


class Provenance(CamelModel):
    financial: str
    tests: str
    code: str
    diagnosis: str
    captured_at: str


class Diagnosis(CamelModel):
    root_cause: str
    explanation: str
    # Phase 1 fixtures say `true` (hand-written text). Live results are model output,
    # so this is `false`. M3 widens the TypeScript type from the literal `true`.
    illustrative: bool = False


class InvestigationResult(CamelModel):
    id: str
    scenario_id: ScenarioId
    mode: Literal["replay", "live"]
    financial: FinancialReport
    diagnosis: Diagnosis
    reference: PatchProposal
    verification: VerificationReport
    code: CodeArtifact
    ast_validation: AstValidation
    logs: "Logs"
    provenance: Provenance


class Logs(CamelModel):
    baseline: str
    reference: str


class ScenarioSummary(CamelModel):
    id: ScenarioId
    title: str
    tag: str
    source_file: str
    test_file: str
    test_count: int
    visual: str


class HealthResponse(CamelModel):
    ok: bool
    live_enabled: bool
    mode: Literal["live", "replay"]
    sandbox_ready: bool | None = None
    queue: dict[str, int] = Field(default_factory=dict)
    limits: dict[str, int] = Field(default_factory=dict)


class StartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: ScenarioId


class StartResponse(CamelModel):
    id: str
    status: str
    position: int = 0


class JobStatusResponse(CamelModel):
    id: str
    status: Literal["queued", "running", "done", "error"]
    scenario_id: ScenarioId
    created_at: str
    stage: str | None = None
    message: str | None = None


class LimitDecision(CamelModel):
    allowed: bool
    reason: str
    retry_after_seconds: int = 0
    remaining_hour: int = 0
    remaining_day: int = 0
    remaining_global: int = 0


AstValidation.model_rebuild()
VerificationReport.model_rebuild()
InvestigationResult.model_rebuild()

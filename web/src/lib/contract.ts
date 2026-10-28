/**
 * RootCause AI — shared result contract.
 *
 * These types mirror the JSON the existing Python backend already produces
 * (`financial_investigator.py`, `proposed_patch.json`, `*_verification_report.json`)
 * and the normalised shape the Phase 2 FastAPI adapter will serve at
 * `/api/investigations/{id}`.
 *
 * Keeping them in one module means switching from replay fixtures to the live
 * adapter is a transport change, never a component rewrite.
 */

export type ScenarioId =
  | "duplicate_transaction"
  | "incorrect_refund"
  | "monetary_precision";

export type Verdict = "verified_fixed" | "not_fixed" | "error";

export type TestState = "pass" | "fail" | "skip";

/** Direct mirror of `financial_investigator.investigate_transactions()` output. */
export interface FinancialReport {
  issue_detected: boolean;
  issue_type: string;
  duplicate_ids: string[];
  affected_transactions: string[];
  actual_total: string;
  expected_total: string;
  discrepancy: string;
}

/** Direct mirror of the Nemotron patch proposal artifact. */
export interface PatchProposal {
  root_cause: string;
  explanation: string;
  target_file: string;
  proposed_code: string;
}

export interface TestCaseResult {
  /** e.g. `test_original_total` */
  name: string;
  /** e.g. `RefundRegressionTests` */
  suite: string;
  /** Outcome against the unmodified, buggy source file. */
  baseline: TestState;
  /** Outcome against the reference repair. */
  reference: TestState;
}

/**
 * Normalised verification report.
 *
 * The raw backend reports are inconsistent across scenarios (the refund report
 * carries `scenario_id: "refund_sign_error"` and omits `elapsed_seconds`;
 * only the duplicate scenario reports `baseline_passed`). Optional fields are
 * therefore explicitly nullable here rather than silently defaulted to 0.
 */
export interface VerificationReport {
  scenarioId: ScenarioId;
  verdict: Verdict;
  expectedTests: number;
  baseline: { ran: number; failed: number };
  reference: { ran: number; failed: number; passed: number };
  attempts: number | null;
  elapsedSeconds: number | null;
  sandbox: string;
  tests: TestCaseResult[];
}

/** Result of running the repository's own `patch_validator.py` structural gate. */
export interface AstValidation {
  passed: boolean;
  reason: string;
  /** Proves the gate is not a rubber stamp: a deliberately malformed patch, rejected. */
  negativeControl: { passed: boolean; reason: string };
}

export interface CodeArtifact {
  /** File name exactly as it exists in the repository. */
  filename: string;
  language: "python";
  original: string;
  candidate: string;
}

export interface Provenance {
  /** Where each part of the displayed evidence came from. */
  financial: string;
  tests: string;
  code: string;
  diagnosis: string;
  capturedAt: string;
}

export interface InvestigationResult {
  id: string;
  scenarioId: ScenarioId;
  mode: "replay" | "live";
  financial: FinancialReport;
  /** Phase 1 has no model output; this is a written explanation, clearly flagged in the UI. */
  diagnosis: {
    rootCause: string;
    explanation: string;
    illustrative: true;
  };
  reference: PatchProposal;
  verification: VerificationReport;
  code: CodeArtifact;
  astValidation: AstValidation;
  logs: { baseline: string; reference: string };
  provenance: Provenance;
}

/** One step of the four-stage investigation pipeline. */
export type StageKey = "investigate" | "diagnose" | "repair" | "verify";

export interface StageDefinition {
  key: StageKey;
  index: string;
  title: string;
  short: string;
  description: string;
  /** Honest label for what the demonstration is doing at this step. */
  replayNote: string;
}

export const STAGES: StageDefinition[] = [
  {
    key: "investigate",
    index: "01",
    title: "Financial investigation",
    short: "Investigate",
    description:
      "Deterministic arithmetic re-totals the ledger independently of the application's own calculator, then classifies the discrepancy.",
    replayNote: "Recomputed from the real transaction records",
  },
  {
    key: "diagnose",
    index: "02",
    title: "Root-cause diagnosis",
    short: "Diagnose",
    description:
      "NVIDIA Nemotron, served through Nebius Token Factory, reads the discrepancy report and the source file and returns a structured diagnosis.",
    replayNote: "Illustrative text — no model call is made in Phase 1",
  },
  {
    key: "repair",
    index: "03",
    title: "Repair generation",
    short: "Repair",
    description:
      "A candidate fix is generated for one function only, then gated by AST validation: signature, decorators and defaults must be unchanged.",
    replayNote: "Reference repair written for this demo — not model output",
  },
  {
    key: "verify",
    index: "04",
    title: "Sandbox verification",
    short: "Verify",
    description:
      "The buggy file and the candidate repair are executed against the same protected regression tests inside a disposable Nebius sandbox.",
    replayNote: "Results produced by running the repository's real test files",
  },
];

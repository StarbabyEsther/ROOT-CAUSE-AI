import measured from "./measured.json";
import { SCENARIOS, type ScenarioMeta } from "./scenarios";
import type {
  InvestigationResult,
  ScenarioId,
  TestCaseResult,
  TestState,
} from "../lib/contract";

/**
 * ============================================================================
 * DEMONSTRATION DATA — PHASE 1
 * ============================================================================
 *
 * What is REAL in this file:
 *   • `financial`      — produced by running the repository's own
 *                        `financial_investigator.investigate_transactions()`
 *                        against each scenario's real transaction records.
 *   • `code`           — the actual source files from the repository, and a
 *                        reference repair written for this demo.
 *   • `verification`   — produced by executing the repository's real regression
 *                        test files against the unmodified buggy source and
 *                        again against the reference repair, on CPython.
 *   • `logs`           — captured stdout of those runs.
 *
 * What is NOT real (and is labelled as such in the UI):
 *   • `diagnosis`      — written by hand. No model was called. NVIDIA Nemotron
 *                        integration exists in the Python backend but is not
 *                        invoked by Phase 1.
 *   • `reference`      — the candidate patch displayed is a hand-written
 *                        reference repair, not Nemotron output.
 *   • Sandbox          — tests ran on local CPython, not inside Nebius.
 *
 * Nothing here claims a live AI execution occurred.
 */

const CAPTURED_AT = "2026-10-26";

const NARRATIVE: Record<
  ScenarioId,
  { rootCause: string; explanation: string }
> = {
  duplicate_transaction: {
    rootCause:
      "calculate_total() iterates every record and never checks whether a transaction has already been processed, so the resent TXN002 payment is counted a second time.",
    explanation:
      "The payment for TXN002 appears twice in the input with identical id, type and amount. Because the loop applies each record unconditionally, the duplicate adds $200.00 to the running total. The ledger itself must stay untouched — the defect is in the accumulation logic, not in the data. A repair keeps a set of processed transaction ids and skips any repeat, which makes the total idempotent without changing stored records.",
  },
  incorrect_refund: {
    rootCause:
      "In the Refund branch, `total += transaction[\"amount\"]` adds the refund instead of subtracting it, inverting the sign of every refund.",
    explanation:
      "RF002 is a $50.00 refund that should reduce the net total. Adding it moves the total $100.00 away from the correct value — once for the amount, and once again because it should have been negative. The marker comment in the source confirms this is an intentional defect. The repair restores `total -= transaction[\"amount\"]`, leaving payments and all records unchanged.",
  },
  monetary_precision: {
    rootCause:
      "The accumulator is a binary float, so decimal amounts are stored approximately and the error is carried through every addition.",
    explanation:
      "0.10 and 0.20 have no exact binary representation, so 0.10 + 0.20 produces 0.30000000000000004 and the subsequent subtraction leaves 0.20000000000000004 instead of 0.20. The residue is about 4×10⁻¹⁷ — far below one cent, which is exactly why a currency-formatted display hides it while an exact-equality assertion fails. The repair accumulates with decimal.Decimal built from str(amount), so every value is represented exactly.",
  },
};

function toState(value: string): TestState {
  if (value === "pass") return "pass";
  if (value === "skip") return "skip";
  return "fail";
}

function suiteName(className: string): string {
  const parts = className.split(".");
  return parts.length > 1 ? parts[parts.length - 2] : className;
}

interface MeasuredScenario {
  sourceFile: string;
  testFile: string;
  baseline: { ran: number; failed: number; ok: boolean };
  reference: { ran: number; failed: number; ok: boolean };
  tests: { name: string; cls: string; baseline: string; reference: string }[];
  originalFunction: string;
  referenceFunction: string;
  baselineOutput: string;
  referenceOutput: string;
  astValidation: {
    passed: boolean;
    reason: string;
    negativeControl: { passed: boolean; reason: string };
  };
}

const measuredScenarios = measured as unknown as Record<ScenarioId, MeasuredScenario>;

function buildRun(scenario: ScenarioMeta): InvestigationResult {
  const data = measuredScenarios[scenario.id];
  const narrative = NARRATIVE[scenario.id];

  const tests: TestCaseResult[] = data.tests.map((test) => ({
    name: test.name,
    suite: suiteName(test.cls),
    baseline: toState(test.baseline),
    reference: toState(test.reference),
  }));

  const passed = data.reference.ran - data.reference.failed;

  return {
    id: `demo-${scenario.id.replace(/_/g, "-")}`,
    scenarioId: scenario.id,
    mode: "replay",
    financial: FINANCIAL[scenario.id],
    diagnosis: {
      rootCause: narrative.rootCause,
      explanation: narrative.explanation,
      illustrative: true,
    },
    reference: {
      root_cause: narrative.rootCause,
      explanation: narrative.explanation,
      target_file: data.sourceFile,
      proposed_code: data.referenceFunction,
    },
    verification: {
      scenarioId: scenario.id,
      verdict: data.reference.ok ? "verified_fixed" : "not_fixed",
      expectedTests: scenario.testCount,
      baseline: { ran: data.baseline.ran, failed: data.baseline.failed },
      reference: { ran: data.reference.ran, failed: data.reference.failed, passed },
      attempts: null,
      elapsedSeconds: null,
      sandbox: "Local CPython · unittest — not a Nebius sandbox run (Phase 2)",
      tests,
    },
    code: {
      filename: data.sourceFile,
      language: "python",
      original: data.originalFunction,
      candidate: data.referenceFunction,
    },
    astValidation: data.astValidation,
    logs: {
      baseline: data.baselineOutput,
      reference: data.referenceOutput,
    },
    provenance: {
      financial:
        "financial_investigator.investigate_transactions() run against this scenario's real records.",
      tests: `${data.testFile} executed against ${data.sourceFile} (baseline) and against the reference repair.`,
      code: `${data.sourceFile} as committed; reference repair written for this demo.`,
      diagnosis: "Hand-written explanation. No model was invoked.",
      capturedAt: CAPTURED_AT,
    },
  };
}

/**
 * Measured by the project's own investigator — see `data/measured.json`.
 * Strings, not numbers, because that is what the backend emits.
 */
const FINANCIAL: Record<ScenarioId, import("../lib/contract").FinancialReport> = {
  duplicate_transaction: {
    issue_detected: true,
    issue_type: "Possible duplicate processing",
    duplicate_ids: ["TXN002"],
    affected_transactions: ["TXN002"],
    actual_total: "600.0",
    expected_total: "400.00",
    discrepancy: "200.00",
  },
  incorrect_refund: {
    issue_detected: true,
    issue_type: "Possible refund sign error",
    duplicate_ids: [],
    affected_transactions: ["RF002"],
    actual_total: "300.0",
    expected_total: "200.00",
    discrepancy: "100.00",
  },
  monetary_precision: {
    issue_detected: true,
    issue_type: "Unclassified financial discrepancy",
    duplicate_ids: [],
    affected_transactions: [],
    actual_total: "0.20000000000000004",
    expected_total: "0.20",
    discrepancy: "4E-17",
  },
};

export const RUNS: Record<ScenarioId, InvestigationResult> = Object.fromEntries(
  SCENARIOS.map((scenario) => [scenario.id, buildRun(scenario)]),
) as Record<ScenarioId, InvestigationResult>;

export const getRun = (id: ScenarioId): InvestigationResult => RUNS[id];

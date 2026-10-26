import type { ScenarioId } from "../lib/contract";

export interface Transaction {
  id: string;
  type: "Payment" | "Refund";
  amount: number;
}

export interface ScenarioMeta {
  id: ScenarioId;
  number: string;
  title: string;
  tag: string;
  blurb: string;
  failure: string;
  sourceFile: string;
  testFile: string;
  testCount: number;
  /** Which visual treatment the investigation dashboard uses for this bug class. */
  visual: "duplicate" | "sign" | "precision";
  emphasis: string;
  records: Transaction[];
}

/**
 * Every record below is copied verbatim from the repository's processors:
 * `transactions.py`, `refund_processor.py`, `precision_processor.py`.
 */
export const SCENARIOS: ScenarioMeta[] = [
  {
    id: "duplicate_transaction",
    number: "01",
    title: "Duplicate transactions",
    tag: "Transaction integrity",
    blurb:
      "A retried payment event is posted twice. The ledger inflates and every downstream settlement is wrong by the duplicated amount.",
    failure: "TXN002 is processed twice, adding $200.00 of phantom revenue.",
    sourceFile: "transactions.py",
    testFile: "test_financial_regression.py",
    testCount: 6,
    visual: "duplicate",
    emphasis: "Idempotency",
    records: [
      { id: "TXN001", type: "Payment", amount: 150.0 },
      { id: "TXN002", type: "Payment", amount: 200.0 },
      { id: "TXN003", type: "Refund", amount: 50.0 },
      { id: "TXN004", type: "Payment", amount: 100.0 },
      { id: "TXN002", type: "Payment", amount: 200.0 },
    ],
  },
  {
    id: "incorrect_refund",
    number: "02",
    title: "Incorrect refunds",
    tag: "Refund reconciliation",
    blurb:
      "A refund is added instead of subtracted. The sign error doubles the refund's impact, so customer credit and net revenue diverge.",
    failure: "RF002 is added to the total instead of deducted.",
    sourceFile: "refund_processor.py",
    testFile: "test_refund_processor.py",
    testCount: 7,
    visual: "sign",
    emphasis: "Sign correctness",
    records: [
      { id: "RF001", type: "Payment", amount: 150.0 },
      { id: "RF002", type: "Refund", amount: 50.0 },
      { id: "RF003", type: "Payment", amount: 100.0 },
    ],
  },
  {
    id: "monetary_precision",
    number: "03",
    title: "Monetary precision",
    tag: "Numerical accuracy",
    blurb:
      "Binary floating point cannot represent decimal money exactly. The error is invisible at two decimal places but breaks exact-equality checks and compounding.",
    failure: "0.10 + 0.20 − 0.10 evaluates to 0.20000000000000004, not 0.20.",
    sourceFile: "precision_processor.py",
    testFile: "test_precision_processor.py",
    testCount: 5,
    visual: "precision",
    emphasis: "Exact decimals",
    records: [
      { id: "PR001", type: "Payment", amount: 0.1 },
      { id: "PR002", type: "Payment", amount: 0.2 },
      { id: "PR003", type: "Refund", amount: 0.1 },
    ],
  },
];

export const getScenario = (id: string | undefined): ScenarioMeta | undefined =>
  SCENARIOS.find((scenario) => scenario.id === id);

export const TOTAL_TESTS = SCENARIOS.reduce((sum, s) => sum + s.testCount, 0);

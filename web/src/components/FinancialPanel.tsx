import { AlertTriangle, ArrowRight, Repeat2, Sigma } from "lucide-react";
import type { FinancialReport } from "../lib/contract";
import type { ScenarioMeta } from "../data/scenarios";
import { Badge } from "./Badge";
import { cn } from "../lib/cn";
import { exactDecimal, money, splitDecimals, superscript } from "../lib/format";

function AmountCell({ amount, precision }: { amount: number; precision: boolean }) {
  return (
    <span className="font-mono text-[0.8125rem] tabular-nums text-ink">
      {precision ? amount.toFixed(2) : money(String(amount))}
    </span>
  );
}

function RecordsTable({ scenario }: { scenario: ScenarioMeta }) {
  const counts = scenario.records.reduce<Record<string, number>>((acc, record) => {
    acc[record.id] = (acc[record.id] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="overflow-hidden rounded-xl border border-white/8">
      <div className="grid grid-cols-[1fr_1fr_1fr_auto] gap-2 border-b border-white/8 bg-white/[0.02] px-4 py-2.5 text-[0.625rem] font-semibold uppercase tracking-[0.14em] text-ink-faint">
        <span>Transaction</span>
        <span>Type</span>
        <span className="text-right">Amount</span>
        <span className="w-28 text-right">Evidence</span>
      </div>
      <div className="divide-y divide-white/5">
        {scenario.records.map((record, index) => {
          const duplicated = scenario.visual === "duplicate" && counts[record.id] > 1;
          const secondOccurrence = duplicated && scenario.records.slice(0, index).some((r) => r.id === record.id);
          const signFault = scenario.visual === "sign" && record.type === "Refund";
          const flagged = secondOccurrence || signFault;

          return (
            <div
              key={`${record.id}-${index}`}
              className={cn(
                "grid grid-cols-[1fr_1fr_1fr_auto] items-center gap-2 px-4 py-2.5 transition-colors",
                flagged ? "bg-rose-400/[0.07]" : "hover:bg-white/[0.02]",
              )}
            >
              <span className="flex items-center gap-2 font-mono text-[0.8125rem] text-ink">
                <span
                  className={cn(
                    "h-1.5 w-1.5 rounded-full",
                    flagged ? "bg-rose-400" : "bg-cyan-400/50",
                  )}
                />
                {record.id}
              </span>
              <span
                className={cn(
                  "text-[0.8125rem]",
                  record.type === "Refund" ? "text-amber-400/90" : "text-ink-muted",
                )}
              >
                {record.type}
              </span>
              <span className="text-right">
                <AmountCell amount={record.amount} precision={scenario.visual === "precision"} />
              </span>
              <span className="w-28 text-right">
                {secondOccurrence && (
                  <Badge tone="rose" className="text-[0.5625rem]">
                    re-posted
                  </Badge>
                )}
                {signFault && !secondOccurrence && (
                  <Badge tone="rose" className="text-[0.5625rem]">
                    sign inverted
                  </Badge>
                )}
                {!flagged && <span className="text-[0.6875rem] text-ink-faint">ok</span>}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function PrecisionInspector({ financial }: { financial: FinancialReport }) {
  const { whole, stable, drift } = splitDecimals(financial.actual_total, financial.expected_total);

  const steps = [
    { label: "Payment PR001", expr: "0.10", value: "0.1", exact: "0.10" },
    { label: "Payment PR002", expr: "0.10 + 0.20", value: "0.30000000000000004", exact: "0.30" },
    { label: "Refund PR003", expr: "0.30000000000000004 − 0.10", value: "0.20000000000000004", exact: "0.20" },
  ];

  return (
    <div className="grid gap-3 lg:grid-cols-2">
      <div className="rounded-xl border border-rose-400/20 bg-rose-400/[0.05] p-4">
        <p className="mb-3 flex items-center gap-2 text-[0.6875rem] font-semibold uppercase tracking-[0.14em] text-rose-400">
          <AlertTriangle className="h-3.5 w-3.5" />
          Binary float · current code
        </p>
        <ul className="space-y-2.5">
          {steps.map((step) => (
            <li key={step.label} className="flex items-baseline justify-between gap-3">
              <span className="text-[0.75rem] text-ink-muted">{step.label}</span>
              <span className="font-mono text-[0.75rem] tabular-nums text-rose-300/90">{step.value}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-xl border border-mint-400/20 bg-mint-400/[0.05] p-4">
        <p className="mb-3 flex items-center gap-2 text-[0.6875rem] font-semibold uppercase tracking-[0.14em] text-mint-400">
          <Sigma className="h-3.5 w-3.5" />
          Decimal · reference repair
        </p>
        <ul className="space-y-2.5">
          {steps.map((step) => (
            <li key={step.label} className="flex items-baseline justify-between gap-3">
              <span className="text-[0.75rem] text-ink-muted">{step.label}</span>
              <span className="font-mono text-[0.75rem] tabular-nums text-mint-400">{step.exact}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="lg:col-span-2 rounded-xl border border-white/8 bg-navy-950/60 p-4">
        <p className="mb-2.5 text-[0.6875rem] font-semibold uppercase tracking-[0.14em] text-ink-faint">
          Digit-level divergence
        </p>
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 font-mono text-[0.9375rem] tabular-nums">
          <span className="text-ink-faint">expected</span>
          <span className="text-mint-400">{financial.expected_total}</span>
          <span className="text-ink-faint">actual</span>
          <span className="text-ink">
            {whole}.{stable}
            <mark className="rounded bg-rose-400/20 px-0.5 text-rose-300">{drift}</mark>
          </span>
        </div>
        <p className="mt-2.5 text-[0.75rem] leading-relaxed text-ink-muted">
          The discrepancy is <span className="font-mono text-rose-300">{exactDecimal(financial.discrepancy)}</span> —
          4 × 10{superscript(-17)} — roughly 14 orders of magnitude below one cent. Currency formatting
          rounds it to <span className="font-mono">$0.00</span>, which is exactly why exact-equality
          assertions catch it and dashboards do not.
        </p>
      </div>
    </div>
  );
}

export function FinancialPanel({
  scenario,
  financial,
}: {
  scenario: ScenarioMeta;
  financial: FinancialReport;
}) {
  const isPrecision = scenario.visual === "precision";

  const story =
    scenario.visual === "duplicate"
      ? `${financial.duplicate_ids.join(", ")} is posted more than once. The independent re-total counts it a single time, so the gap equals the duplicated amount.`
      : scenario.visual === "sign"
        ? `Adding a refund instead of subtracting it moves the total by twice the refund amount — once for the value, once for the inverted sign.`
        : `Floating-point representation error accumulates through the sum. The total drifts below one cent but fails exact decimal comparison.`;

  return (
    <div className="card overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/8 px-5 py-3.5">
        <div className="flex items-center gap-2.5">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-cyan-400/25 bg-cyan-400/10">
            <Repeat2 className="h-3.5 w-3.5 text-cyan-300" />
          </span>
          <p className="text-[0.8125rem] font-medium text-white">Financial investigation</p>
        </div>
        <Badge tone={financial.issue_type === "Unclassified financial discrepancy" ? "amber" : "rose"} dot>
          {financial.issue_type}
        </Badge>
      </div>

      <div className="grid gap-5 p-5 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <div className="flex flex-col justify-between gap-4">
          <div>
            <p className="text-[0.6875rem] font-semibold uppercase tracking-[0.14em] text-ink-faint">
              Discrepancy
            </p>
            <p className="mt-2 font-mono text-[clamp(2rem,4.4vw,2.9rem)] leading-none tabular-nums text-rose-300">
              {isPrecision ? (
                <span className="text-[clamp(1.5rem,3.2vw,2.1rem)]">
                  4 × 10{superscript(-17)}
                </span>
              ) : (
                money(financial.discrepancy)
              )}
            </p>
            <p className="mt-2.5 text-[0.75rem] leading-relaxed text-ink-muted">
              Calculated independently of the application's own calculator.
            </p>
          </div>

          <dl className="grid grid-cols-2 gap-3">
            <div className="rounded-xl border border-white/8 bg-navy-950/50 p-3">
              <dt className="text-[0.625rem] font-semibold uppercase tracking-[0.12em] text-ink-faint">
                Reported total
              </dt>
              <dd className="mt-1.5 font-mono text-[0.9375rem] tabular-nums text-rose-300">
                {isPrecision ? financial.actual_total : money(financial.actual_total)}
              </dd>
            </div>
            <div className="rounded-xl border border-white/8 bg-navy-950/50 p-3">
              <dt className="text-[0.625rem] font-semibold uppercase tracking-[0.12em] text-ink-faint">
                Expected total
              </dt>
              <dd className="mt-1.5 font-mono text-[0.9375rem] tabular-nums text-mint-400">
                {isPrecision ? financial.expected_total : money(financial.expected_total)}
              </dd>
            </div>
          </dl>
        </div>

        <div className="flex flex-col gap-3">
          <p className="text-[0.75rem] font-semibold uppercase tracking-[0.14em] text-ink-faint">
            Ledger under investigation
          </p>
          <RecordsTable scenario={scenario} />
          <p className="flex items-start gap-2 text-[0.75rem] leading-relaxed text-ink-muted">
            <ArrowRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-cyan-400" />
            {story}
          </p>
        </div>
      </div>

      {isPrecision && (
        <div className="border-t border-white/8 p-5">
          <PrecisionInspector financial={financial} />
        </div>
      )}
    </div>
  );
}

import { useMemo } from "react";
import {
  BadgeCheck,
  CircleCheck,
  CircleSlash,
  Download,
  FlaskConical,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react";
import type { InvestigationResult, TestCaseResult } from "../lib/contract";
import type { ScenarioMeta } from "../data/scenarios";
import { Badge } from "./Badge";
import { LogViewer } from "./LogViewer";
import { cn } from "../lib/cn";

const StateChip = ({ state, label }: { state: "pass" | "fail" | "skip"; label: string }) => (
  <span
    className={cn(
      "inline-flex w-[4.5rem] items-center justify-center gap-1.5 rounded-md border px-2 py-1 font-mono text-[0.625rem]",
      state === "pass" && "border-mint-400/25 bg-mint-400/10 text-mint-400",
      state === "fail" && "border-rose-400/25 bg-rose-400/10 text-rose-400",
      state === "skip" && "border-white/12 bg-white/5 text-ink-faint",
    )}
  >
    {state === "pass" ? "PASS" : state === "fail" ? "FAIL" : "SKIP"}
    <span className="sr-only">{label}</span>
  </span>
);

function SummaryColumn({
  title,
  subtitle,
  passed,
  failed,
  total,
  tone,
}: {
  title: string;
  subtitle: string;
  passed: number;
  failed: number;
  total: number;
  tone: "rose" | "mint";
}) {
  const ratio = total > 0 ? (passed / total) * 100 : 0;
  return (
    <div
      className={cn(
        "rounded-xl border p-4",
        tone === "rose" ? "border-rose-400/20 bg-rose-400/[0.04]" : "border-mint-400/20 bg-mint-400/[0.04]",
      )}
    >
      <p className="text-[0.6875rem] font-semibold uppercase tracking-[0.14em] text-ink-faint">{title}</p>
      <p className="mt-1 text-[0.6875rem] text-ink-muted">{subtitle}</p>
      <div className="mt-3 flex items-end gap-2">
        <span
          className={cn(
            "font-mono text-[1.75rem] leading-none tabular-nums",
            tone === "rose" ? "text-rose-300" : "text-mint-400",
          )}
        >
          {passed}
        </span>
        <span className="pb-0.5 font-mono text-[0.8125rem] text-ink-faint">/ {total} passed</span>
      </div>
      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/8">
        <div
          className={cn("h-full rounded-full", tone === "rose" ? "bg-rose-400/70" : "bg-mint-400/80")}
          style={{ width: `${ratio}%` }}
        />
      </div>
      <p className="mt-2 font-mono text-[0.6875rem] text-ink-faint">
        {failed} failing · {total} ran
      </p>
    </div>
  );
}

export function VerificationPanel({
  run,
  scenario,
}: {
  run: InvestigationResult;
  scenario: ScenarioMeta;
}) {
  const { verification, astValidation } = run;
  const verified = verification.verdict === "verified_fixed";
  const total = verification.reference.ran;
  const baselinePassed = verification.baseline.ran - verification.baseline.failed;

  const reportBlob = useMemo(() => {
    const payload = {
      product: "RootCause AI",
      mode: "demonstration",
      scenario_id: run.scenarioId,
      note: "Phase 1 demonstration. Reference repair, not Nemotron output. Tests executed on local CPython.",
      financial: run.financial,
      verification: verification,
      ast_validation: astValidation,
      provenance: run.provenance,
    };
    return `data:application/json;charset=utf-8,${encodeURIComponent(JSON.stringify(payload, null, 2))}`;
  }, [run, verification, astValidation]);

  return (
    <div className="card overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/8 px-5 py-3.5">
        <div className="flex items-center gap-2.5">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-cyan-400/25 bg-cyan-400/10">
            <FlaskConical className="h-3.5 w-3.5 text-cyan-300" />
          </span>
          <p className="text-[0.8125rem] font-medium text-white">Verification &amp; test evidence</p>
        </div>
        <Badge tone="neutral">executed, not simulated</Badge>
      </div>

      <div className="space-y-5 p-5">
        <div
          className={cn(
            "flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center",
            verified ? "border-mint-400/25 bg-mint-400/[0.06]" : "border-amber-400/25 bg-amber-400/[0.06]",
          )}
        >
          <span
            className={cn(
              "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border",
              verified
                ? "border-mint-400/30 bg-mint-400/10 text-mint-400"
                : "border-amber-400/30 bg-amber-400/10 text-amber-400",
            )}
          >
            {verified ? <BadgeCheck className="h-5 w-5" /> : <TriangleAlert className="h-5 w-5" />}
          </span>
          <div className="min-w-0 flex-1">
            <p className="font-display text-[1.0625rem] font-semibold text-white">
              {verified
                ? `Reference repair passes all ${total} protected tests`
                : "No passing repair for this run"}
            </p>
            <p className="mt-0.5 text-[0.75rem] leading-relaxed text-ink-muted">
              {verified
                ? `The buggy source fails ${verification.baseline.failed} of ${verification.baseline.ran}. The candidate repair fails none.`
                : "The candidate repair did not satisfy the protected suite."}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge tone={verified ? "mint" : "amber"} dot>
              {verification.verdict}
            </Badge>
            <Badge tone="neutral">{total} tests</Badge>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <SummaryColumn
            title="Baseline"
            subtitle={`Unmodified ${scenario.sourceFile}`}
            passed={baselinePassed}
            failed={verification.baseline.failed}
            total={verification.baseline.ran}
            tone="rose"
          />
          <SummaryColumn
            title="Candidate"
            subtitle="Reference repair applied to a copy"
            passed={verification.reference.passed}
            failed={verification.reference.failed}
            total={verification.reference.ran}
            tone="mint"
          />
        </div>

        <div>
          <div className="mb-2 flex items-end justify-between">
            <p className="text-[0.75rem] font-semibold uppercase tracking-[0.14em] text-ink-faint">
              Protected regression suite
            </p>
            <p className="font-mono text-[0.6875rem] text-ink-faint">{scenario.testFile}</p>
          </div>
          <div className="overflow-hidden rounded-xl border border-white/8">
            <div className="grid grid-cols-[1fr_auto_auto] gap-3 border-b border-white/8 bg-white/[0.02] px-4 py-2 text-[0.625rem] font-semibold uppercase tracking-[0.12em] text-ink-faint">
              <span>Test</span>
              <span className="text-center">Baseline</span>
              <span className="text-center">Candidate</span>
            </div>
            <div className="divide-y divide-white/5">
              {verification.tests.map((test: TestCaseResult) => (
                <div
                  key={test.name}
                  className="grid grid-cols-[1fr_auto_auto] items-center gap-3 px-4 py-2 transition-colors hover:bg-white/[0.02]"
                >
                  <span className="flex min-w-0 flex-col">
                    <span className="truncate font-mono text-[0.75rem] text-ink">{test.name}</span>
                    <span className="truncate text-[0.625rem] text-ink-faint">{test.suite}</span>
                  </span>
                  <StateChip state={test.baseline} label={`${test.name} baseline ${test.baseline}`} />
                  <StateChip state={test.reference} label={`${test.name} candidate ${test.reference}`} />
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="grid gap-3 lg:grid-cols-2">
          <div className="rounded-xl border border-white/8 bg-navy-950/50 p-4">
            <p className="flex items-center gap-2 text-[0.6875rem] font-semibold uppercase tracking-[0.14em] text-ink-faint">
              <ShieldCheck className="h-3.5 w-3.5 text-cyan-400" />
              Structural gate
            </p>
            <p className="mt-2 flex items-start gap-2 text-[0.75rem] leading-relaxed text-ink-muted">
              <CircleCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-mint-400" />
              <span>
                <span className="font-mono text-[0.6875rem] text-ink">patch_validator.py</span> —{" "}
                {astValidation.reason}
              </span>
            </p>
            <p className="mt-2 flex items-start gap-2 text-[0.75rem] leading-relaxed text-ink-faint">
              <CircleSlash className="mt-0.5 h-3.5 w-3.5 shrink-0 text-rose-400" />
              <span>
                Control: a two-function patch was rejected — “{astValidation.negativeControl.reason}”
              </span>
            </p>
          </div>

          <div className="rounded-xl border border-white/8 bg-navy-950/50 p-4">
            <p className="text-[0.6875rem] font-semibold uppercase tracking-[0.14em] text-ink-faint">
              Execution environment
            </p>
            <p className="mt-2 font-mono text-[0.75rem] leading-relaxed text-ink-muted">
              {verification.sandbox}
            </p>
            <p className="mt-2 text-[0.6875rem] leading-relaxed text-ink-faint">
              Live runs execute both variants inside disposable Nebius sandboxes via the Contree CLI,
              twice per investigation. Phase 2 wires that path to this panel.
            </p>
          </div>
        </div>

        <LogViewer baseline={run.logs.baseline} reference={run.logs.reference} />

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-white/8 pt-4">
          <p className="max-w-md text-[0.6875rem] leading-relaxed text-ink-faint">
            Passing this suite is bounded evidence, not a proof of correctness for all inputs.
          </p>
          <a
            href={reportBlob}
            download={`rootcause_${run.scenarioId}_demo_report.json`}
            className="inline-flex items-center gap-2 rounded-full border border-white/12 bg-white/[0.03] px-4 py-2 text-[0.75rem] font-medium text-ink transition-colors hover:border-cyan-400/40 hover:text-white"
          >
            <Download className="h-3.5 w-3.5" />
            Download report (JSON)
          </a>
        </div>
      </div>
    </div>
  );
}

import { Brain, Info, ShieldQuestion } from "lucide-react";
import type { InvestigationResult } from "../lib/contract";
import { Badge } from "./Badge";

export function DiagnosisPanel({ run }: { run: InvestigationResult }) {
  return (
    <div className="card overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/8 px-5 py-3.5">
        <div className="flex items-center gap-2.5">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-blue-400/25 bg-blue-500/10">
            <Brain className="h-3.5 w-3.5 text-blue-300" />
          </span>
          <p className="text-[0.8125rem] font-medium text-white">Root-cause diagnosis</p>
        </div>
        <Badge tone="amber" dot>
          Illustrative — no model call
        </Badge>
      </div>

      <div className="grid gap-5 p-5 lg:grid-cols-[1.55fr_1fr]">
        <div className="space-y-4">
          <div className="rounded-xl border-l-2 border-cyan-400/60 bg-white/[0.025] px-4 py-3">
            <p className="mb-1.5 text-[0.625rem] font-semibold uppercase tracking-[0.14em] text-cyan-300">
              Suspected root cause
            </p>
            <p className="text-[0.875rem] leading-relaxed text-ink">{run.diagnosis.rootCause}</p>
          </div>
          <p className="text-[0.8125rem] leading-relaxed text-ink-muted">{run.diagnosis.explanation}</p>
          <p className="flex items-start gap-2 rounded-lg border border-amber-400/20 bg-amber-400/[0.06] px-3 py-2.5 text-[0.6875rem] leading-relaxed text-amber-200/90">
            <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            This text was written by hand to describe the defect. In the live pipeline the same panel
            is filled from NVIDIA Nemotron's structured JSON response.
          </p>
        </div>

        <div className="space-y-3 rounded-xl border border-white/8 bg-navy-950/50 p-4">
          <p className="flex items-center gap-2 text-[0.625rem] font-semibold uppercase tracking-[0.14em] text-ink-faint">
            <ShieldQuestion className="h-3.5 w-3.5" />
            Live pipeline contract
          </p>
          <dl className="space-y-2.5 text-[0.75rem]">
            {[
              ["Model", "NVIDIA Nemotron"],
              ["Served via", "Nebius Token Factory"],
              ["Returns", "JSON object only"],
              ["Fields", "issue_type · affected_function · root_cause · suggested_fix"],
            ].map(([label, value]) => (
              <div key={label} className="flex flex-col gap-0.5">
                <dt className="text-[0.6875rem] text-ink-faint">{label}</dt>
                <dd className="font-mono text-[0.6875rem] leading-relaxed text-ink-muted">{value}</dd>
              </div>
            ))}
          </dl>
          <p className="hairline-t pt-2.5 text-[0.6875rem] leading-relaxed text-ink-faint">
            A diagnosis is a hypothesis. Nothing in RootCause AI is reported as fixed until tests
            agree.
          </p>
        </div>
      </div>
    </div>
  );
}

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, CheckCircle2, Play, Wrench } from "lucide-react";
import { PageHero } from "../components/PageHero";
import { usePageTitle } from "../lib/usePageTitle";
import { ScenarioCard } from "../components/ScenarioCard";
import { Button, ButtonLink } from "../components/Button";
import { DemoBanner } from "../components/DemoBanner";
import { Badge } from "../components/Badge";
import { SCENARIOS, getScenario } from "../data/scenarios";
import { RUNS } from "../data/runs";
import { money } from "../lib/format";
import { cn } from "../lib/cn";

export default function Lab() {
  usePageTitle("Investigation Lab");
  const [selected, setSelected] = useState(SCENARIOS[0].id);
  const navigate = useNavigate();
  const scenario = getScenario(selected)!;
  const run = RUNS[scenario.id];

  return (
    <div className="pb-24">
      <PageHero
        eyebrow="Investigation lab"
        title={
          <>
            Choose a defect. Watch the pipeline
            <span className="text-ink-faint"> earn its verdict.</span>
          </>
        }
        description="Three synthetic financial defects, each with its own protected regression suite. Select a scenario to inspect the ledger, then run the four-stage investigation."
      >
        <DemoBanner />
      </PageHero>

      <div className="mx-auto max-w-[82rem] px-4 sm:px-6 lg:px-8">
        <div className="grid gap-4 md:grid-cols-3">
          {SCENARIOS.map((item, index) => (
            <ScenarioCard
              key={item.id}
              scenario={item}
              index={index}
              selected={selected === item.id}
              onSelect={() => setSelected(item.id)}
            />
          ))}
        </div>

        <motion.div
          key={scenario.id}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="mt-6 grid gap-4 lg:grid-cols-[1.35fr_1fr]"
        >
          <div className="card overflow-hidden">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/8 px-5 py-3.5">
              <div className="flex items-center gap-2.5">
                <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-rose-400/25 bg-rose-400/10">
                  <Wrench className="h-3.5 w-3.5 text-rose-300" />
                </span>
                <p className="text-[0.8125rem] font-medium text-white">{scenario.title}</p>
              </div>
              <Badge tone="neutral" className="font-mono">
                {scenario.sourceFile}
              </Badge>
            </div>

            <div className="space-y-4 p-5">
              <div className="rounded-xl border-l-2 border-rose-400/60 bg-white/[0.02] px-4 py-3">
                <p className="text-[0.625rem] font-semibold uppercase tracking-[0.14em] text-rose-300">
                  Failure signature
                </p>
                <p className="mt-1.5 font-mono text-[0.75rem] leading-relaxed text-ink">
                  {scenario.failure}
                </p>
              </div>

              <div className="grid grid-cols-3 gap-3">
                {[
                  {
                    label: "Reported",
                    // Currency rounding would hide a sub-cent float drift entirely.
                    value:
                      scenario.visual === "precision"
                        ? run.financial.actual_total
                        : money(run.financial.actual_total),
                    tone: "text-rose-300",
                  },
                  {
                    label: "Expected",
                    value:
                      scenario.visual === "precision"
                        ? run.financial.expected_total
                        : money(run.financial.expected_total),
                    tone: "text-mint-400",
                  },
                  {
                    label: "Tests failing",
                    value: `${run.verification.baseline.failed} / ${run.verification.baseline.ran}`,
                    tone: "text-ink",
                  },
                ].map((item) => (
                  <div key={item.label} className="rounded-xl border border-white/8 bg-navy-950/50 p-3">
                    <p className="text-[0.5625rem] uppercase tracking-[0.12em] text-ink-faint">
                      {item.label}
                    </p>
                    <p className={cn("mt-1 font-mono text-[0.75rem] tabular-nums", item.tone)}>
                      {item.value}
                    </p>
                  </div>
                ))}
              </div>

              <div>
                <p className="mb-2 text-[0.625rem] font-semibold uppercase tracking-[0.14em] text-ink-faint">
                  Synthetic records ({scenario.records.length})
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {scenario.records.map((record, index) => (
                    <span
                      key={`${record.id}-${index}`}
                      className={cn(
                        "inline-flex items-center gap-1.5 rounded-md border px-2 py-1 font-mono text-[0.625rem]",
                        scenario.records
                          .slice(0, index)
                          .some((earlier) => earlier.id === record.id)
                          ? "border-rose-400/25 bg-rose-400/[0.08] text-rose-300"
                          : "border-white/8 bg-white/[0.03] text-ink-muted",
                      )}
                    >
                      {record.id}
                      <span className="text-ink-faint">{record.type === "Payment" ? "+" : "−"}</span>
                      {record.amount.toFixed(2)}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="card flex flex-col gap-4 p-5">
            <div>
              <p className="text-[0.625rem] font-semibold uppercase tracking-[0.14em] text-ink-faint">
                What will run
              </p>
              <ol className="mt-3 space-y-2.5">
                {[
                  "Re-total the ledger independently",
                  "Diagnose the root cause (Nemotron in live mode)",
                  "Generate a candidate repair (AST-gated)",
                  `Run ${scenario.testCount} protected tests, baseline vs candidate`,
                ].map((item, index) => (
                  <li key={item} className="flex items-start gap-2.5 text-[0.75rem] leading-relaxed text-ink-muted">
                    <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-white/12 font-mono text-[0.5625rem] text-ink-faint">
                      {index + 1}
                    </span>
                    {item}
                  </li>
                ))}
              </ol>
            </div>

            <div className="rounded-xl border border-white/8 bg-navy-950/50 p-3">
              <p className="flex items-center gap-1.5 text-[0.625rem] text-ink-faint">
                <CheckCircle2 className="h-3 w-3 text-mint-400" />
                Recorded evidence available
              </p>
              <p className="mt-1 text-[0.6875rem] leading-relaxed text-ink-muted">
                This scenario already has measured figures, test outcomes and a reference diff.
              </p>
            </div>

            <div className="mt-auto flex flex-col gap-2">
              <Button onClick={() => navigate(`/lab/${scenario.id}`)} className="w-full">
                <Play className="h-3.5 w-3.5" />
                Run investigation
              </Button>
              <ButtonLink to="/architecture" variant="ghost" size="sm" className="w-full">
                How the pipeline is wired
                <ArrowRight className="h-3.5 w-3.5" />
              </ButtonLink>
            </div>
          </div>
        </motion.div>

        <div className="mt-8 grid gap-3 sm:grid-cols-3">
          {[
            ["Deterministic first", "The financial investigator does not call a model. Arithmetic is arithmetic."],
            ["Proposal, not deploy", "Candidate repairs are never written into the repository."],
            ["Bounded claims", "Passing a scenario suite is scoped evidence, not universal correctness."],
          ].map(([title, body]) => (
            <div key={title} className="rounded-xl border border-white/8 bg-white/[0.02] p-4">
              <p className="text-[0.75rem] font-medium text-white">{title}</p>
              <p className="mt-1 text-[0.6875rem] leading-relaxed text-ink-muted">{body}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

import { AnimatePresence, motion } from "framer-motion";
import { Check, Loader2, Play, RotateCcw, Square, Sparkles } from "lucide-react";
import { STAGES, type ScenarioId, type StageKey } from "../lib/contract";
import type { ScenarioMeta } from "../data/scenarios";
import { useInvestigation } from "../lib/useInvestigation";
import { Badge } from "./Badge";
import { Button } from "./Button";
import { DemoBanner, ModePill } from "./DemoBanner";
import { FinancialPanel } from "./FinancialPanel";
import { DiagnosisPanel } from "./DiagnosisPanel";
import { CodeCompare } from "./CodeCompare";
import { VerificationPanel } from "./VerificationPanel";
import { StageProgress } from "./StageProgress";
import { ProvenancePanel } from "./ProvenancePanel";
import { cn } from "../lib/cn";

function StageNode({ index, status }: { index: string; status: "pending" | "running" | "done" }) {
  return (
    <span
      className={cn(
        "relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border text-[0.6875rem] font-semibold transition-all duration-500",
        status === "done" && "border-cyan-400/50 bg-cyan-400/12 text-cyan-300",
        status === "running" && "animate-pulse-ring border-cyan-400/60 bg-navy-800 text-cyan-300",
        status === "pending" && "border-white/10 bg-navy-900 text-ink-faint",
      )}
    >
      {status === "done" ? <Check className="h-4 w-4" /> : index}
    </span>
  );
}

function WorkingState({ stage }: { stage: (typeof STAGES)[number] }) {
  const labels: Record<StageKey, string> = {
    investigate: "Re-totalling the ledger independently…",
    diagnose: "A live run would now query NVIDIA Nemotron…",
    repair: "A live run would now generate a candidate patch…",
    verify: "A live run would now execute the protected tests…",
  };

  return (
    <div className="relative overflow-hidden rounded-xl border border-white/8 bg-navy-950/60 p-4">
      <div className="flex items-center gap-2.5">
        <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />
        <p className="text-[0.8125rem] text-ink">{labels[stage.key]}</p>
      </div>
      <p className="mt-1.5 pl-6 text-[0.6875rem] text-ink-faint">{stage.replayNote}</p>
      <div className="mt-3 space-y-2 pl-6">
        {[88, 64, 76].map((width, index) => (
          <div
            key={width}
            className="sheen h-2 rounded-full bg-white/[0.05]"
            style={{ width: `${width}%`, animationDelay: `${index * 0.25}s` }}
          />
        ))}
      </div>
    </div>
  );
}

export function InvestigationWorkspace({
  scenario,
  autoStart = false,
}: {
  scenario: ScenarioMeta;
  autoStart?: boolean;
}) {
  const { states, result, running, elapsed, start, stop, fallbackNotice, mode } = useInvestigation(
    scenario.id as ScenarioId,
    autoStart,
  );

  const stageContent: Record<StageKey, React.ReactNode> = result
    ? {
        investigate: <FinancialPanel scenario={scenario} financial={result.financial} />,
        diagnose: <DiagnosisPanel run={result} />,
        repair: <CodeCompare code={result.code} />,
        verify: <VerificationPanel run={result} scenario={scenario} />,
      }
    : ({} as Record<StageKey, React.ReactNode>);

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-4 rounded-2xl border border-white/8 bg-white/[0.02] p-4 sm:p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="font-display text-[1.25rem] font-semibold text-white">{scenario.title}</h1>
              <Badge tone="neutral" className="font-mono">
                {scenario.sourceFile}
              </Badge>
            </div>
            <p className="mt-1.5 max-w-2xl text-[0.8125rem] leading-relaxed text-ink-muted">
              {scenario.blurb}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {mode && <ModePill mode={mode} />}
            {running ? (
              <Button variant="secondary" size="sm" onClick={stop}>
                <Square className="h-3 w-3" />
                Stop
              </Button>
            ) : (
              <Button size="sm" onClick={start}>
                {result ? <RotateCcw className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
                {result ? "Replay run" : "Run demonstration"}
              </Button>
            )}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-[0.6875rem]">
          <Badge tone="cyan" dot>
            {scenario.testCount} protected tests
          </Badge>
          <Badge tone="blue">NVIDIA Nemotron · Nebius</Badge>
          <Badge tone="neutral">Deterministic investigator</Badge>
          <Badge tone="neutral">AST-gated patch</Badge>
          <span className="ml-auto inline-flex items-center gap-1.5 text-ink-faint">
            <Sparkles className="h-3 w-3" />
            {scenario.emphasis}
          </span>
        </div>

        <DemoBanner compact mode={mode} fallbackMessage={fallbackNotice?.message} />
      </div>

      <StageProgress states={states} elapsed={elapsed} running={running} />

      <div className="space-y-0">
        {STAGES.map((stage, index) => {
          const state = states[stage.key];
          const done = state.status === "done";
          const active = state.status === "running";

          return (
            <div key={stage.key} className="grid grid-cols-[auto_1fr] gap-4">
              <div className="flex flex-col items-center">
                <StageNode index={stage.index} status={state.status} />
                {index < STAGES.length - 1 && (
                  <div
                    className={cn(
                      "w-px flex-1 transition-colors duration-700",
                      done ? "bg-gradient-to-b from-cyan-400/45 to-cyan-400/10" : "bg-white/8",
                    )}
                  />
                )}
              </div>

              <div className={cn("pb-7", index === STAGES.length - 1 && "pb-0")}>
                <div className="mb-2.5 flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-baseline gap-2.5">
                    <p className="text-[0.625rem] font-semibold uppercase tracking-[0.16em] text-ink-faint">
                      Stage {stage.index}
                    </p>
                    <h2
                      className={cn(
                        "font-display text-[0.9375rem] font-semibold transition-colors",
                        done || active ? "text-white" : "text-ink-faint",
                      )}
                    >
                      {stage.title}
                    </h2>
                  </div>
                  {done && state.completedAt !== null && (
                    <span className="font-mono text-[0.625rem] tabular-nums text-ink-faint">
                      t+{(state.completedAt / 1000).toFixed(1)}s
                    </span>
                  )}
                </div>

                {!done && !active && (
                  <p className="max-w-2xl text-[0.75rem] leading-relaxed text-ink-faint">
                    {stage.description}
                  </p>
                )}

                <AnimatePresence mode="wait" initial={false}>
                  {active && (
                    <motion.div
                      key="working"
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -4 }}
                      transition={{ duration: 0.28 }}
                    >
                      <WorkingState stage={stage} />
                    </motion.div>
                  )}

                  {done && (
                    <motion.div
                      key="done"
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
                    >
                      {stageContent[stage.key]}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          );
        })}
      </div>

      {result && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="space-y-3 pt-2"
        >
          <ProvenancePanel run={result} />
        </motion.div>
      )}
    </div>
  );
}

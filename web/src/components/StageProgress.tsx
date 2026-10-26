import { Check } from "lucide-react";
import { motion } from "framer-motion";
import { STAGES } from "../lib/contract";
import type { StageState } from "../lib/useInvestigation";
import type { StageKey } from "../lib/contract";
import { cn } from "../lib/cn";

export function StageProgress({
  states,
  elapsed,
  running,
}: {
  states: Record<StageKey, StageState>;
  elapsed: number;
  running: boolean;
}) {
  const completed = STAGES.filter((stage) => states[stage.key].status === "done").length;
  const progress = (completed / STAGES.length) * 100;

  return (
    <div className="card px-4 py-4 sm:px-5">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-[0.6875rem] font-semibold uppercase tracking-[0.14em] text-ink-faint">
          Investigation pipeline
        </p>
        <p className="font-mono text-[0.6875rem] tabular-nums text-ink-faint">
          {running ? `${(elapsed / 1000).toFixed(1)}s elapsed` : completed === 4 ? "complete" : "idle"}
        </p>
      </div>

      <div className="relative">
        <div className="absolute left-0 right-0 top-[0.6875rem] h-px bg-white/8" />
        <motion.div
          className="absolute left-0 top-[0.6875rem] h-px bg-gradient-to-r from-blue-500 to-cyan-400"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        />
        <ol className="relative grid grid-cols-4 gap-2">
          {STAGES.map((stage) => {
            const state = states[stage.key];
            const done = state.status === "done";
            const active = state.status === "running";
            return (
              <li key={stage.key} className="flex flex-col items-start gap-2">
                <span
                  className={cn(
                    "flex h-[1.375rem] w-[1.375rem] items-center justify-center rounded-full border text-[0.5625rem] font-semibold transition-colors duration-500",
                    done && "border-cyan-400/60 bg-cyan-400/15 text-cyan-300",
                    active && "animate-pulse-ring border-cyan-400/70 bg-navy-900 text-cyan-300",
                    !done && !active && "border-white/12 bg-navy-900 text-ink-faint",
                  )}
                >
                  {done ? <Check className="h-3 w-3" /> : stage.index}
                </span>
                <span
                  className={cn(
                    "text-[0.6875rem] font-medium leading-tight transition-colors duration-500",
                    done || active ? "text-ink" : "text-ink-faint",
                  )}
                >
                  {stage.short}
                </span>
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}

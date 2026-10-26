import { ArrowUpRight } from "lucide-react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import type { ScenarioMeta } from "../data/scenarios";
import { RUNS } from "../data/runs";
import { money } from "../lib/format";
import { cn } from "../lib/cn";

export function ScenarioCard({
  scenario,
  index = 0,
  selected = false,
  onSelect,
  className,
}: {
  scenario: ScenarioMeta;
  index?: number;
  selected?: boolean;
  onSelect?: () => void;
  className?: string;
}) {
  const run = RUNS[scenario.id];
  const precision = scenario.visual === "precision";

  const body = (
    <>
      <div className="flex items-center justify-between">
        <span className="font-mono text-[0.625rem] uppercase tracking-[0.16em] text-ink-faint">
          {scenario.number} / {scenario.tag}
        </span>
        <span
          className={cn(
            "flex h-6 w-6 items-center justify-center rounded-full border transition-colors",
            selected
              ? "border-cyan-400/50 bg-cyan-400/15 text-cyan-300"
              : "border-white/10 text-ink-faint group-hover:border-cyan-400/40 group-hover:text-cyan-300",
          )}
        >
          <ArrowUpRight className="h-3 w-3" />
        </span>
      </div>

      <h3 className="mt-3 text-[1.0625rem] font-semibold text-white">{scenario.title}</h3>
      <p className="mt-1.5 text-[0.75rem] leading-relaxed text-ink-muted">{scenario.blurb}</p>

      <div className="mt-4 flex items-end justify-between gap-3 border-t border-white/[0.06] pt-3">
        <div>
          <p className="text-[0.5625rem] uppercase tracking-[0.14em] text-ink-faint">Discrepancy</p>
          <p className="mt-0.5 font-mono text-[0.9375rem] tabular-nums text-rose-300">
            {precision ? "4 × 10⁻¹⁷" : money(run.financial.discrepancy)}
          </p>
        </div>
        <div className="text-right">
          <p className="text-[0.5625rem] uppercase tracking-[0.14em] text-ink-faint">Protected tests</p>
          <p className="mt-0.5 font-mono text-[0.9375rem] text-ink">
            {scenario.testCount}
            <span className="ml-1 text-[0.6875rem] text-ink-faint">
              ({run.verification.baseline.failed} failing)
            </span>
          </p>
        </div>
      </div>
    </>
  );

  const shell = cn(
    "card card-hover group flex flex-col p-4 text-left",
    selected && "border-cyan-400/45 bg-cyan-400/[0.04]",
    className,
  );

  if (onSelect) {
    return (
      <motion.button
        type="button"
        onClick={onSelect}
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-60px" }}
        transition={{ duration: 0.45, delay: index * 0.07 }}
        className={shell}
        aria-pressed={selected}
      >
        {body}
      </motion.button>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.45, delay: index * 0.07 }}
    >
      <Link to={`/lab/${scenario.id}`} className={shell}>
        {body}
      </Link>
    </motion.div>
  );
}

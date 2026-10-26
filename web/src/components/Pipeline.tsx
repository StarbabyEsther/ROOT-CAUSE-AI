import { Brain, FileCode2, ScanSearch, ShieldCheck } from "lucide-react";
import { motion } from "framer-motion";
import { STAGES } from "../lib/contract";
import { cn } from "../lib/cn";

const ICONS = {
  investigate: ScanSearch,
  diagnose: Brain,
  repair: FileCode2,
  verify: ShieldCheck,
} as const;

const ARTIFACTS = {
  investigate: "financial_report.json",
  diagnose: "structured JSON diagnosis",
  repair: "proposed_patch.json",
  verify: "sandbox_report.json",
} as const;

export function Pipeline({ compact = false }: { compact?: boolean }) {
  return (
    <div
      className={cn(
        "relative grid gap-3",
        compact ? "sm:grid-cols-2 lg:grid-cols-4" : "md:grid-cols-2 xl:grid-cols-4",
      )}
    >
      {STAGES.map((stage, index) => {
        const Icon = ICONS[stage.key];
        return (
          <motion.div
            key={stage.key}
            initial={{ opacity: 0, y: 18 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.5, delay: index * 0.08 }}
            className="card card-hover group relative flex flex-col gap-3 p-4"
          >
            <div className="flex items-center justify-between">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl border border-cyan-400/25 bg-cyan-400/[0.08] text-cyan-300 transition-colors group-hover:border-cyan-400/50">
                <Icon className="h-4 w-4" />
              </span>
              <span className="font-mono text-[0.6875rem] text-ink-faint">{stage.index}</span>
            </div>
            <div>
              <h3 className="text-[0.9375rem] font-semibold text-white">{stage.short}</h3>
              <p className="mt-1.5 text-[0.75rem] leading-relaxed text-ink-muted">{stage.description}</p>
            </div>
            <div className="mt-auto flex items-center gap-1.5 border-t border-white/[0.06] pt-2.5">
              <span className="h-1 w-1 rounded-full bg-cyan-400/60" />
              <span className="truncate font-mono text-[0.625rem] text-ink-faint">{ARTIFACTS[stage.key]}</span>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}

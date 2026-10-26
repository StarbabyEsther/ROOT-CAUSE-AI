import { motion, useReducedMotion } from "framer-motion";
import { Check, ShieldCheck, TriangleAlert } from "lucide-react";
import { RUNS } from "../data/runs";
import { getScenario } from "../data/scenarios";
import { money } from "../lib/format";
import { cn } from "../lib/cn";

/** Stylised preview of the investigation dashboard. Demonstration data. */
export function HeroVisual() {
  const reduce = useReducedMotion();
  const run = RUNS.duplicate_transaction;
  const scenario = getScenario("duplicate_transaction")!;
  const tests = run.verification.tests;

  return (
    <div className="relative mx-auto w-full max-w-[30rem]">
      <div
        aria-hidden
        className="absolute -inset-6 rounded-[2rem] bg-[radial-gradient(ellipse_at_30%_20%,rgba(46,107,255,0.30),transparent_60%),radial-gradient(ellipse_at_75%_80%,rgba(34,211,238,0.22),transparent_62%)] blur-2xl"
      />

      <motion.div
        initial={{ opacity: 0, y: 24, rotateX: 6 }}
        animate={{ opacity: 1, y: 0, rotateX: 0 }}
        transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1], delay: 0.15 }}
        className="card relative overflow-hidden p-0"
      >
        <div className="flex items-center justify-between border-b border-white/8 px-4 py-2.5">
          <div className="flex items-center gap-2">
            <span className="flex gap-1.5">
              <span className="h-2 w-2 rounded-full bg-white/15" />
              <span className="h-2 w-2 rounded-full bg-white/15" />
              <span className="h-2 w-2 rounded-full bg-white/15" />
            </span>
            <span className="ml-1 font-mono text-[0.625rem] text-ink-faint">investigation / {run.scenarioId}</span>
          </div>
          <span className="inline-flex items-center gap-1 rounded-full border border-mint-400/30 bg-mint-400/10 px-2 py-0.5 text-[0.5625rem] font-medium uppercase tracking-[0.1em] text-mint-400">
            <ShieldCheck className="h-2.5 w-2.5" />
            verified
          </span>
        </div>

        <div className="space-y-4 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-[0.5625rem] font-semibold uppercase tracking-[0.16em] text-ink-faint">
                Discrepancy detected
              </p>
              <p className="mt-1 font-mono text-[2rem] leading-none tabular-nums text-rose-300">
                {money(run.financial.discrepancy)}
              </p>
            </div>
            <div className="rounded-lg border border-rose-400/25 bg-rose-400/[0.08] px-2 py-1.5 text-center">
              <p className="font-mono text-[0.625rem] text-rose-300">TXN002</p>
              <p className="text-[0.5625rem] text-ink-faint">re-posted</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {[
              ["Reported", money(run.financial.actual_total), "text-rose-300"],
              ["Expected", money(run.financial.expected_total), "text-mint-400"],
            ].map(([label, value, tone]) => (
              <div key={label} className="rounded-lg border border-white/8 bg-navy-950/50 px-2.5 py-2">
                <p className="text-[0.5625rem] uppercase tracking-[0.12em] text-ink-faint">{label}</p>
                <p className={cn("mt-0.5 font-mono text-[0.75rem] tabular-nums", tone)}>{value}</p>
              </div>
            ))}
          </div>

          <div>
            <div className="mb-1.5 flex items-center justify-between">
              <p className="text-[0.5625rem] font-semibold uppercase tracking-[0.14em] text-ink-faint">
                Protected tests
              </p>
              <p className="font-mono text-[0.5625rem] text-mint-400">
                {run.verification.reference.passed}/{run.verification.reference.ran} pass
              </p>
            </div>
            <div className="space-y-1">
              {tests.slice(0, 4).map((test, index) => (
                <motion.div
                  key={test.name}
                  initial={{ opacity: 0, x: -6 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 + index * 0.09, duration: 0.4 }}
                  className="flex items-center justify-between rounded-md bg-white/[0.025] px-2 py-1.5"
                >
                  <span className="truncate font-mono text-[0.625rem] text-ink-muted">{test.name}</span>
                  <span className="flex items-center gap-1 text-[0.5625rem]">
                    <span className="text-rose-400/70">FAIL</span>
                    <span className="text-ink-faint">→</span>
                    <span className="flex items-center gap-0.5 text-mint-400">
                      <Check className="h-2.5 w-2.5" />
                      PASS
                    </span>
                  </span>
                </motion.div>
              ))}
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between border-t border-white/8 bg-navy-950/40 px-4 py-2">
          <span className="font-mono text-[0.5625rem] text-ink-faint">{scenario.sourceFile}</span>
          <span className="font-mono text-[0.5625rem] text-ink-faint">calculate_total()</span>
        </div>
      </motion.div>

      <motion.div
        animate={reduce ? undefined : { y: [0, -8, 0] }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
        className="absolute -left-4 bottom-10 hidden rounded-xl border border-white/10 bg-navy-900/95 px-3 py-2 shadow-[0_18px_40px_-20px_rgba(3,7,15,0.9)] backdrop-blur sm:block"
      >
        <p className="text-[0.5625rem] uppercase tracking-[0.12em] text-ink-faint">Root cause</p>
        <p className="mt-0.5 font-mono text-[0.6875rem] text-cyan-300">missing idempotency check</p>
      </motion.div>

      <motion.div
        animate={reduce ? undefined : { y: [0, 9, 0] }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut", delay: 0.8 }}
        className="absolute -right-3 top-24 hidden items-center gap-1.5 rounded-xl border border-amber-400/25 bg-navy-900/95 px-2.5 py-1.5 shadow-[0_18px_40px_-20px_rgba(3,7,15,0.9)] backdrop-blur sm:flex"
      >
        <TriangleAlert className="h-3 w-3 text-amber-400" />
        <span className="font-mono text-[0.625rem] text-amber-200/90">3 baseline failures</span>
      </motion.div>
    </div>
  );
}

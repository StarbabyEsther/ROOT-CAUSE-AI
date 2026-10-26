import { BookLock, ChevronDown } from "lucide-react";
import { useState } from "react";
import type { InvestigationResult } from "../lib/contract";
import { cn } from "../lib/cn";

const ROWS: { key: keyof Omit<InvestigationResult["provenance"], "capturedAt">; label: string }[] = [
  { key: "financial", label: "Financial figures" },
  { key: "tests", label: "Test outcomes" },
  { key: "code", label: "Source & patch" },
  { key: "diagnosis", label: "Diagnosis text" },
];

export function ProvenancePanel({ run }: { run: InvestigationResult }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-xl border border-white/8 bg-navy-950/40">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
        aria-expanded={open}
      >
        <span className="flex items-center gap-2 text-[0.75rem] font-medium text-ink">
          <BookLock className="h-3.5 w-3.5 text-cyan-400" />
          How this evidence was produced
        </span>
        <span className="flex items-center gap-2 text-[0.6875rem] text-ink-faint">
          <span className="hidden sm:inline">captured {run.provenance.capturedAt}</span>
          <ChevronDown className={cn("h-4 w-4 transition-transform duration-300", open && "rotate-180")} />
        </span>
      </button>
      {open && (
        <dl className="grid gap-3 border-t border-white/8 px-4 py-3.5 sm:grid-cols-2">
          {ROWS.map((row) => (
            <div key={row.key}>
              <dt className="text-[0.625rem] font-semibold uppercase tracking-[0.12em] text-ink-faint">
                {row.label}
              </dt>
              <dd className="mt-1 text-[0.75rem] leading-relaxed text-ink-muted">
                {run.provenance[row.key]}
              </dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}

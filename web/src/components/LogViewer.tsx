import { useState } from "react";
import { ChevronDown, Terminal } from "lucide-react";
import { cn } from "../lib/cn";

export function LogViewer({
  baseline,
  reference,
}: {
  baseline: string;
  reference: string;
}) {
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<"baseline" | "reference">("baseline");
  const text = tab === "baseline" ? baseline : reference;

  return (
    <div className="rounded-xl border border-white/8 bg-navy-950/60">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
        aria-expanded={open}
      >
        <span className="flex items-center gap-2 text-[0.75rem] font-medium text-ink">
          <Terminal className="h-3.5 w-3.5 text-cyan-400" />
          Captured test output
        </span>
        <ChevronDown
          className={cn("h-4 w-4 text-ink-faint transition-transform duration-300", open && "rotate-180")}
        />
      </button>

      {open && (
        <div className="border-t border-white/8">
          <div className="flex gap-1 px-3 pt-2.5">
            {(["baseline", "reference"] as const).map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setTab(option)}
                className={cn(
                  "rounded-md px-2.5 py-1 text-[0.6875rem] capitalize transition-colors",
                  tab === option
                    ? option === "baseline"
                      ? "bg-rose-400/15 text-rose-300"
                      : "bg-mint-400/12 text-mint-400"
                    : "text-ink-faint hover:text-ink",
                )}
              >
                {option === "baseline" ? "buggy source" : "reference repair"}
              </button>
            ))}
          </div>
          <pre className="max-h-72 overflow-auto px-4 py-3 font-mono text-[0.6875rem] leading-relaxed text-ink-muted">
            {text}
          </pre>
        </div>
      )}
    </div>
  );
}

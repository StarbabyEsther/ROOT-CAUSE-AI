import { useMemo, useState } from "react";
import { Check, Columns2, GitCompareArrows } from "lucide-react";
import type { CodeArtifact } from "../lib/contract";
import { countChanges, diffLines, type DiffLine } from "../lib/diff";
import { cn } from "../lib/cn";
import { Badge } from "./Badge";

function Line({
  line,
  tone,
}: {
  line?: DiffLine;
  tone: "left" | "right";
}) {
  if (!line) {
    return <div className="h-[1.55rem]" aria-hidden />;
  }

  const { text, mark } = line;
  const before = mark ? text.slice(0, mark[0]) : text;
  const changed = mark ? text.slice(mark[0], mark[1]) : "";
  const after = mark ? text.slice(mark[1]) : "";

  return (
    <div className="flex min-h-[1.55rem] items-start">
      <span
        className={cn(
          "w-9 shrink-0 select-none pr-2 text-right font-mono text-[0.6875rem] leading-[1.55rem] tabular-nums",
          "text-white/20",
        )}
      >
        {line.number}
      </span>
      <code className="whitespace-pre font-mono text-[0.75rem] leading-[1.55rem] text-ink/90">
        {before}
        {changed && (
          <mark
            className={cn(
              "rounded px-0.5",
              tone === "left"
                ? "bg-rose-400/25 text-rose-200"
                : "bg-mint-400/22 text-mint-200",
            )}
          >
            {changed}
          </mark>
        )}
        {after}
      </code>
    </div>
  );
}

export function CodeCompare({ code }: { code: CodeArtifact }) {
  const [view, setView] = useState<"split" | "unified">("split");
  const rows = useMemo(() => diffLines(code.original, code.candidate), [code]);
  const changes = useMemo(() => countChanges(rows), [rows]);

  return (
    <div className="card overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/8 px-5 py-3.5">
        <div className="flex items-center gap-2.5">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-mint-400/25 bg-mint-400/10">
            <GitCompareArrows className="h-3.5 w-3.5 text-mint-400" />
          </span>
          <div>
            <p className="text-[0.8125rem] font-medium text-white">
              <span className="font-mono text-[0.8125rem]">{code.filename}</span>
              <span className="ml-2 text-[0.75rem] font-normal text-ink-faint">calculate_total()</span>
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono text-[0.6875rem] text-ink-faint">
            <span className="text-rose-300">−{changes.removed}</span>{" "}
            <span className="text-mint-400">+{changes.added}</span>
          </span>
          <div className="flex rounded-lg border border-white/10 p-0.5">
            {(["split", "unified"] as const).map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setView(option)}
                className={cn(
                  "rounded-md px-2 py-1 text-[0.6875rem] capitalize transition-colors",
                  view === option ? "bg-white/10 text-white" : "text-ink-faint hover:text-ink",
                )}
              >
                {option}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 border-b border-white/8 bg-navy-950/40 text-[0.6875rem]">
        <div className="flex items-center gap-2 px-4 py-2.5 text-ink-muted">
          <span className="h-1.5 w-1.5 rounded-full bg-rose-400" />
          Original · committed source
        </div>
        <div className="flex items-center gap-2 border-l border-white/8 px-4 py-2.5 text-ink-muted">
          <span className="h-1.5 w-1.5 rounded-full bg-mint-400" />
          Candidate · reference repair
        </div>
      </div>

      {view === "split" ? (
        <div className="overflow-x-auto">
          <div className="min-w-[38rem]">
            {rows.map((row, index) => (
              <div
                key={index}
                className={cn(
                  "grid grid-cols-2 border-b border-white/[0.03] last:border-0",
                  row.kind === "change" && "bg-white/[0.015]",
                  row.kind === "left-only" && "bg-rose-500/[0.06]",
                  row.kind === "right-only" && "bg-mint-500/[0.06]",
                )}
              >
                <div className="border-r border-white/[0.04] py-0.5">
                  <Line line={row.left} tone="left" />
                </div>
                <div className="py-0.5">
                  <Line line={row.right} tone="right" />
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="overflow-x-auto p-4">
          <div className="min-w-[32rem]">
            {rows.map((row, index) => {
              if (row.kind === "same") {
                return (
                  <div key={index} className="flex">
                    <span className="w-6 shrink-0 text-center font-mono text-[0.6875rem] leading-[1.55rem] text-white/20">
                      {" "}
                    </span>
                    <code className="whitespace-pre font-mono text-[0.75rem] leading-[1.55rem] text-ink/80">
                      {row.left?.text}
                    </code>
                  </div>
                );
              }
              return (
                <div key={index}>
                  {row.left && (
                    <div className="flex bg-rose-500/[0.08]">
                      <span className="w-6 shrink-0 text-center font-mono text-[0.6875rem] leading-[1.55rem] text-rose-400">
                        −
                      </span>
                      <code className="whitespace-pre font-mono text-[0.75rem] leading-[1.55rem] text-rose-200">
                        {row.left.text}
                      </code>
                    </div>
                  )}
                  {row.right && (
                    <div className="flex bg-mint-500/[0.07]">
                      <span className="w-6 shrink-0 text-center font-mono text-[0.6875rem] leading-[1.55rem] text-mint-400">
                        +
                      </span>
                      <code className="whitespace-pre font-mono text-[0.75rem] leading-[1.55rem] text-mint-200">
                        {row.right.text}
                      </code>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-white/8 bg-navy-950/40 px-5 py-3">
        <span className="flex items-center gap-1.5 text-[0.6875rem] text-ink-faint">
          <Columns2 className="h-3 w-3" />
          Only <span className="font-mono">calculate_total()</span> may change
        </span>
        <span className="flex items-center gap-1.5 text-[0.6875rem] text-ink-faint">
          <Check className="h-3 w-3 text-mint-400" />
          Records, imports and helpers preserved
        </span>
        <Badge tone="neutral" className="ml-auto text-[0.5625rem]">
          proposal only — never auto-applied
        </Badge>
      </div>
    </div>
  );
}

import { Info, X } from "lucide-react";
import { useState } from "react";
import { API_MODE } from "../lib/api";

/**
 * Always-visible honesty affordance. Phase 1 never claims a live AI execution:
 * every investigation on this site is a replay of recorded demonstration data.
 */
export function DemoBanner({ compact = false }: { compact?: boolean }) {
  const [dismissed, setDismissed] = useState(false);
  if (dismissed) return null;

  return (
    <div className="relative overflow-hidden rounded-xl border border-cyan-400/20 bg-cyan-400/[0.05] px-3.5 py-2.5 sm:px-4">
      <div className="flex items-start gap-2.5">
        <Info className="mt-px h-3.5 w-3.5 shrink-0 text-cyan-300" />
        <p className="pr-5 text-[0.75rem] leading-relaxed text-ink-muted">
          <span className="font-medium text-cyan-200">
            {API_MODE === "live" ? "Live mode" : "Demonstration mode"}
          </span>
          {compact
            ? " — recorded run. No model is called."
            : " — these investigations replay recorded evidence. Financial figures and test outcomes were produced by the project's real Python modules; the diagnosis text and candidate patch are hand-written reference material, and no NVIDIA Nemotron call is made in Phase 1."}
        </p>
      </div>
      <button
        type="button"
        onClick={() => setDismissed(true)}
        className="absolute right-2 top-2 rounded-md p-1 text-ink-faint transition-colors hover:text-white"
        aria-label="Dismiss demonstration notice"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

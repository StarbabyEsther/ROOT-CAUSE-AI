import { Info, X, RadioTower, FlaskConical } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchHealth, PREFERRED_MODE, type Health } from "../lib/api";
import { cn } from "../lib/cn";

/**
 * Honesty affordance.
 *
 * Every investigation on this site is labelled with what actually produced it:
 *   • Live  — NVIDIA Nemotron + Nebius sandbox really ran
 *   • Recorded — a replay of a measurement, no model call
 *
 * The label is derived from the runtime result's `mode`, not from the build
 * configuration, so a fallback can never be presented as a live execution.
 */
export function DemoBanner({
  compact = false,
  mode = null,
  fallbackMessage,
}: {
  compact?: boolean;
  /** The mode of the result currently on screen, if any. */
  mode?: "live" | "replay" | null;
  fallbackMessage?: string | null;
}) {
  const [dismissed, setDismissed] = useState(false);
  const [health, setHealth] = useState<Health | null>(null);

  useEffect(() => {
    if (PREFERRED_MODE !== "live") return;
    const controller = new AbortController();
    void fetchHealth(controller.signal).then(setHealth);
    return () => controller.abort();
  }, []);

  if (dismissed) return null;

  // A fallback is the strongest signal: it explains why this run is not live.
  if (fallbackMessage) {
    return (
      <div className="relative overflow-hidden rounded-xl border border-amber-400/25 bg-amber-400/[0.07] px-3.5 py-2.5 sm:px-4">
        <div className="flex items-start gap-2.5">
          <FlaskConical className="mt-px h-3.5 w-3.5 shrink-0 text-amber-400" />
          <p className="pr-5 text-[0.75rem] leading-relaxed text-ink-muted">
            <span className="font-medium text-amber-200">Recorded demonstration</span> — {fallbackMessage}
          </p>
        </div>
        <button
          type="button"
          onClick={() => setDismissed(true)}
          className="absolute right-2 top-2 rounded-md p-1 text-ink-faint transition-colors hover:text-white"
          aria-label="Dismiss notice"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    );
  }

  const isLive = mode === "live";
  const known = mode !== null;

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl border px-3.5 py-2.5 sm:px-4",
        isLive ? "border-mint-400/25 bg-mint-400/[0.06]" : "border-cyan-400/20 bg-cyan-400/[0.05]",
      )}
    >
      <div className="flex items-start gap-2.5">
        {isLive ? (
          <RadioTower className="mt-px h-3.5 w-3.5 shrink-0 text-mint-400" />
        ) : (
          <Info className="mt-px h-3.5 w-3.5 shrink-0 text-cyan-300" />
        )}
        <p className="pr-5 text-[0.75rem] leading-relaxed text-ink-muted">
          {isLive ? (
            <>
              <span className="font-medium text-mint-300">Live investigation</span> — NVIDIA Nemotron
              generated the diagnosis and repair, and the protected suite ran in a disposable Nebius
              sandbox. Verification is reported from that run.
            </>
          ) : known ? (
            <>
              <span className="font-medium text-cyan-200">Recorded demonstration</span> — this is a
              replay of a measured investigation. Financial figures and test outcomes came from the
              project's real Python modules; the diagnosis text is reference material and no model was
              called.
            </>
          ) : (
            <>
              <span className="font-medium text-cyan-200">
                {PREFERRED_MODE === "live" && health?.liveEnabled ? "Live mode ready" : "Demonstration mode"}
              </span>
              {compact
                ? " — recorded run unless stated otherwise."
                : PREFERRED_MODE === "live" && health?.liveEnabled
                  ? " — runs execute the real pipeline; if the service is unavailable or a limit is reached you will see a recorded investigation, labelled as such."
                  : " — investigations replay recorded evidence. Financial figures and test outcomes were produced by the project's real Python modules; the diagnosis text is illustrative and no Nemotron call is made."}
            </>
          )}
        </p>
      </div>
      <button
        type="button"
        onClick={() => setDismissed(true)}
        className="absolute right-2 top-2 rounded-md p-1 text-ink-faint transition-colors hover:text-white"
        aria-label="Dismiss notice"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

/** Small pill for headers, driven by the same runtime mode. */
export function ModePill({ mode }: { mode: "live" | "replay" | null }) {
  const isLive = mode === "live";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[0.625rem] font-semibold uppercase tracking-[0.14em]",
        isLive
          ? "border-mint-400/30 bg-mint-400/10 text-mint-400"
          : "border-cyan-400/25 bg-cyan-400/[0.07] text-cyan-300",
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", isLive ? "bg-mint-400" : "bg-cyan-400")} />
      {isLive ? "Live" : "Recorded"}
    </span>
  );
}

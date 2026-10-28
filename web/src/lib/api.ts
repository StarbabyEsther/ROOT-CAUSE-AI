/**
 * Transport layer.
 *
 * Two modes, one contract:
 *   • replay — recorded demonstration data, plays on a compressed timeline
 *   • live   — POST /api/investigations against the FastAPI adapter, then SSE
 *
 * The UI never has to know which one produced a result: both yield an
 * `InvestigationResult` whose `mode` field drives the labelling.
 *
 * Safety net: if live mode is requested but the service is disabled, rate
 * limited, or unreachable, we fall back to the recorded run **and say so**.
 * Replay is never blocked, and a fallback is never silently presented as live.
 *
 * No credential, key or token is referenced in this file. The browser only calls
 * same-origin `/api` routes.
 */
import type { InvestigationResult, ScenarioId, StageKey } from "./contract";
import { RUNS } from "../data/runs";

/** Build-time preference. Runtime health can still downgrade this. */
export const PREFERRED_MODE: "replay" | "live" =
  import.meta.env.VITE_API_MODE === "live" ? "live" : "replay";

/**
 * Base URL for the adapter.
 *
 * Empty (the default) means same-origin `/api/*`, which is what the dev proxy and
 * a Pages Function both provide. Set `VITE_API_BASE=https://api.example.com` only
 * when the API is served from a different origin; the adapter's CORS allowlist
 * must include this site's origin in that case.
 */
export const API_BASE = (import.meta.env.VITE_API_BASE ?? "").replace(/\/$/, "");

const apiUrl = (path: string) => `${API_BASE}${path}`;

export interface StageEvent {
  stage: StageKey;
  status: "running" | "done";
}

export type LiveUnavailableReason =
  | "live_disabled"
  | "per_ip_hour"
  | "per_ip_day"
  | "global_day"
  | "concurrent_limit"
  | "unreachable"
  | "failed";

export interface RunHandlers {
  onStage: (event: StageEvent) => void;
  onComplete: (result: InvestigationResult) => void;
  /** Live could not proceed; the caller falls back to replay. */
  onFallback: (reason: LiveUnavailableReason, message: string) => void;
  /** A live run started and then failed — no silent success. */
  onError: (message: string) => void;
}

export interface Health {
  ok: boolean;
  liveEnabled: boolean;
  mode: "live" | "replay";
}

const FALLBACK_MESSAGES: Record<LiveUnavailableReason, string> = {
  live_disabled:
    "Live investigations are switched off on the server. You are seeing a recorded investigation.",
  per_ip_hour: "Hourly demonstration limit reached. You are seeing a recorded investigation.",
  per_ip_day: "Daily demonstration limit reached. You are seeing a recorded investigation.",
  global_day: "The shared daily limit for live runs is used up. You are seeing a recorded investigation.",
  concurrent_limit: "Another visitor is running an investigation. You are seeing a recorded investigation.",
  unreachable: "The investigation service is not reachable. You are seeing a recorded investigation.",
  failed: "The live investigation could not complete. You are seeing a recorded investigation.",
};

const replayTiming: { stage: StageKey; duration: number }[] = [
  { stage: "investigate", duration: 900 },
  { stage: "diagnose", duration: 1900 },
  { stage: "repair", duration: 1700 },
  { stage: "verify", duration: 2100 },
];

export function playReplay(
  scenarioId: ScenarioId,
  handlers: Pick<RunHandlers, "onStage" | "onComplete">,
  speed = 1,
): () => void {
  const timers: number[] = [];
  let elapsed = 0;
  let cancelled = false;

  replayTiming.forEach(({ stage, duration }) => {
    const scaled = duration * speed;
    timers.push(
      window.setTimeout(() => {
        if (!cancelled) handlers.onStage({ stage, status: "running" });
      }, elapsed),
    );
    elapsed += scaled;
    timers.push(
      window.setTimeout(() => {
        if (!cancelled) handlers.onStage({ stage, status: "done" });
      }, elapsed),
    );
  });

  timers.push(
    window.setTimeout(() => {
      if (!cancelled) handlers.onComplete(RUNS[scenarioId]);
    }, elapsed + 200),
  );

  return () => {
    cancelled = true;
    timers.forEach((timer) => window.clearTimeout(timer));
  };
}

const fallback = (reason: LiveUnavailableReason, handlers: RunHandlers) => {
  handlers.onFallback(reason, FALLBACK_MESSAGES[reason]);
};

/** Probe the adapter so the UI can label itself honestly before a run starts. */
export async function fetchHealth(signal?: AbortSignal): Promise<Health | null> {
  if (PREFERRED_MODE !== "live") return null;
  try {
    const response = await fetch(apiUrl("/api/health"), { signal, headers: { accept: "application/json" } });
    if (!response.ok) return null;
    const body = (await response.json()) as Health;
    return { ok: Boolean(body.ok), liveEnabled: Boolean(body.liveEnabled), mode: body.mode };
  } catch {
    return null;
  }
}

function startLive(scenarioId: ScenarioId, handlers: RunHandlers): () => void {
  const controller = new AbortController();
  let source: EventSource | undefined;
  let finished = false;

  const start = async () => {
    let response: Response;
    try {
      response = await fetch(apiUrl("/api/investigations"), {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ scenario_id: scenarioId }),
        signal: controller.signal,
      });
    } catch (error) {
      if ((error as Error).name === "AbortError") return;
      fallback("unreachable", handlers);
      return;
    }

    if (response.status === 503 || response.status === 429) {
      const detail = await response.json().catch(() => ({}));
      const reason = (detail?.detail?.error ?? "live_disabled") as LiveUnavailableReason;
      fallback(reason in FALLBACK_MESSAGES ? reason : "failed", handlers);
      return;
    }

    if (!response.ok) {
      fallback("failed", handlers);
      return;
    }

    const { id } = (await response.json()) as { id: string };

    source = new EventSource(apiUrl(`/api/investigations/${id}/events`));
    source.addEventListener("stage", (event) => {
      const data = JSON.parse((event as MessageEvent).data) as { stage: StageKey; status: "running" | "done" };
      handlers.onStage({ stage: data.stage, status: data.status });
    });
    source.addEventListener("result", (event) => {
      finished = true;
      source?.close();
      handlers.onComplete(JSON.parse((event as MessageEvent).data) as InvestigationResult);
    });
    source.addEventListener("error", () => {
      source?.close();
      if (finished) return;
      // The stream dropped after the run began: report it, never fake a result.
      handlers.onError("The live investigation stream ended unexpectedly. Please try again.");
    });
  };

  void start();

  return () => {
    controller.abort();
    source?.close();
  };
}

/**
 * Starts an investigation and returns a cancel function.
 * Live mode degrades to replay, with an explicit reason reported to the caller.
 */
export function startInvestigation(scenarioId: ScenarioId, handlers: RunHandlers): () => void {
  if (PREFERRED_MODE === "live") return startLive(scenarioId, handlers);
  return playReplay(scenarioId, handlers);
}

export { FALLBACK_MESSAGES };

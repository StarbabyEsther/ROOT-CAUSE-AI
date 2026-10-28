/**
 * Transport layer.
 *
 * Phase 1 runs entirely on recorded demonstration data (`replay`). Phase 2 adds
 * a FastAPI adapter and flips `VITE_API_MODE=live`; nothing in the UI changes
 * because both modes emit the same `InvestigationResult` contract.
 *
 * No credential, key or token is referenced anywhere in this file — the browser
 * only ever talks to same-origin `/api` routes (proxied by Vite in dev, by the
 * host in production).
 */
import type { InvestigationResult, ScenarioId, StageKey } from "./contract";
import { RUNS } from "../data/runs";

export const API_MODE: "replay" | "live" =
  import.meta.env.VITE_API_MODE === "live" ? "live" : "replay";

export interface StageEvent {
  stage: StageKey;
  status: "running" | "done";
}

export interface RunHandlers {
  onStage: (event: StageEvent) => void;
  onComplete: (result: InvestigationResult) => void;
  onError: (message: string) => void;
}

/** Approximate wall-clock the real pipeline spends in each stage. */
const REPLAY_TIMING: { stage: StageKey; duration: number }[] = [
  { stage: "investigate", duration: 900 },
  { stage: "diagnose", duration: 1900 },
  { stage: "repair", duration: 1700 },
  { stage: "verify", duration: 2100 },
];

function replayInvestigation(scenarioId: ScenarioId, handlers: RunHandlers): () => void {
  const timers: number[] = [];
  let elapsed = 0;
  let cancelled = false;

  REPLAY_TIMING.forEach(({ stage, duration }) => {
    timers.push(
      window.setTimeout(() => {
        if (!cancelled) handlers.onStage({ stage, status: "running" });
      }, elapsed),
    );
    elapsed += duration;
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

/**
 * Phase 2 implementation, kept here so the swap is a one-line mode change.
 * POST creates the run; the event stream reports stage transitions.
 */
function liveInvestigation(scenarioId: ScenarioId, handlers: RunHandlers): () => void {
  const controller = new AbortController();
  let source: EventSource | undefined;

  const start = async () => {
    try {
      const response = await fetch("/api/investigations", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ scenario_id: scenarioId }),
        signal: controller.signal,
      });
      if (!response.ok) throw new Error(`Adapter responded ${response.status}`);
      const { id } = (await response.json()) as { id: string };

      source = new EventSource(`/api/investigations/${id}/events`);
      source.addEventListener("stage", (event) => {
        handlers.onStage(JSON.parse((event as MessageEvent).data) as StageEvent);
      });
      source.addEventListener("result", (event) => {
        handlers.onComplete(JSON.parse((event as MessageEvent).data) as InvestigationResult);
        source?.close();
      });
      source.addEventListener("error", () => {
        handlers.onError("Lost connection to the investigation service.");
        source?.close();
      });
    } catch (error) {
      if ((error as Error).name !== "AbortError") {
        handlers.onError((error as Error).message);
      }
    }
  };

  void start();

  return () => {
    controller.abort();
    source?.close();
  };
}

/**
 * Starts an investigation and returns a cancel function.
 * Replay mode plays the recorded run on a compressed timeline.
 */
export function startInvestigation(scenarioId: ScenarioId, handlers: RunHandlers): () => void {
  return API_MODE === "live"
    ? liveInvestigation(scenarioId, handlers)
    : replayInvestigation(scenarioId, handlers);
}

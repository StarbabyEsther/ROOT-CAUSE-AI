import { useCallback, useEffect, useRef, useState } from "react";
import type { InvestigationResult, ScenarioId, StageKey } from "./contract";
import { STAGES } from "./contract";
import { startInvestigation, type StageEvent } from "./api";

export type StageStatus = "pending" | "running" | "done";

export interface StageState {
  status: StageStatus;
  completedAt: number | null;
}

const initialStates = (): Record<StageKey, StageState> =>
  Object.fromEntries(STAGES.map((stage) => [stage.key, { status: "pending", completedAt: null }])) as Record<
    StageKey,
    StageState
  >;

export function useInvestigation(scenarioId: ScenarioId, autoStart = false) {
  const [states, setStates] = useState(initialStates);
  const [result, setResult] = useState<InvestigationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const cancelRef = useRef<(() => void) | null>(null);
  const startedAt = useRef<number>(0);

  const stop = useCallback(() => {
    cancelRef.current?.();
    cancelRef.current = null;
    setRunning(false);
  }, []);

  const start = useCallback(() => {
    stop();
    setStates(initialStates());
    setResult(null);
    setError(null);
    setRunning(true);
    startedAt.current = performance.now();
    setElapsed(0);

    cancelRef.current = startInvestigation(scenarioId, {
      onStage: (event: StageEvent) => {
        setStates((current) => ({
          ...current,
          [event.stage]: {
            status: event.status,
            completedAt: event.status === "done" ? performance.now() - startedAt.current : null,
          },
        }));
      },
      onComplete: (next) => {
        setResult(next);
        setRunning(false);
        cancelRef.current = null;
      },
      onError: (message) => {
        setError(message);
        setRunning(false);
        cancelRef.current = null;
      },
    });
  }, [scenarioId, stop]);

  useEffect(() => {
    if (!running) return;
    const timer = window.setInterval(() => setElapsed(performance.now() - startedAt.current), 100);
    return () => window.clearInterval(timer);
  }, [running]);

  useEffect(() => {
    if (autoStart) start();
    return () => stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenarioId]);

  return { states, result, error, running, elapsed, start, stop };
}

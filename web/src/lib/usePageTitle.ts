import { useEffect } from "react";

const BASE = "RootCause AI";
const DEFAULT = `${BASE} — Autonomous Financial Software Debugging`;

export function usePageTitle(title?: string) {
  useEffect(() => {
    document.title = title ? `${title} — ${BASE}` : DEFAULT;
    return () => {
      document.title = DEFAULT;
    };
  }, [title]);
}

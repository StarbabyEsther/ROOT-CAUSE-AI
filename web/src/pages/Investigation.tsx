import { Link, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { InvestigationWorkspace } from "../components/InvestigationWorkspace";
import { SCENARIOS, getScenario } from "../data/scenarios";
import { cn } from "../lib/cn";
import { usePageTitle } from "../lib/usePageTitle";
import NotFound from "./NotFound";

export default function Investigation() {
  const { scenarioId } = useParams();
  const scenario = getScenario(scenarioId);

  usePageTitle(scenario?.title ?? "Not found");

  if (!scenario) return <NotFound />;

  return (
    <div className="pb-24 pt-24 sm:pt-28">
      <div className="mx-auto max-w-[82rem] px-4 sm:px-6 lg:px-8">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <Link
            to="/lab"
            className="inline-flex items-center gap-1.5 text-[0.75rem] text-ink-muted transition-colors hover:text-white"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Investigation lab
          </Link>

          <nav aria-label="Scenario switcher" className="flex flex-wrap gap-1.5">
            {SCENARIOS.map((item) => (
              <Link
                key={item.id}
                to={`/lab/${item.id}`}
                className={cn(
                  "rounded-full border px-2.5 py-1 text-[0.6875rem] transition-colors",
                  item.id === scenario.id
                    ? "border-cyan-400/40 bg-cyan-400/10 text-cyan-300"
                    : "border-white/10 text-ink-faint hover:border-white/20 hover:text-ink",
                )}
              >
                {item.title}
              </Link>
            ))}
          </nav>
        </div>

        <InvestigationWorkspace key={scenario.id} scenario={scenario} autoStart />
      </div>
    </div>
  );
}

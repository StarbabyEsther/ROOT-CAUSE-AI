import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-[70vh] items-center justify-center px-6 pt-24">
      <div className="text-center">
        <p className="font-mono text-[0.6875rem] uppercase tracking-[0.2em] text-cyan-300">404</p>
        <h1 className="mt-3 text-[2rem]">No investigation at this address.</h1>
        <p className="mx-auto mt-3 max-w-sm text-[0.875rem] text-ink-muted">
          The scenario you requested is not in the registry. Three are available in the lab.
        </p>
        <Link
          to="/lab"
          className="mt-6 inline-flex items-center gap-2 rounded-full bg-blue-500 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-400"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to the lab
        </Link>
      </div>
    </div>
  );
}

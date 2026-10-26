import { Link } from "react-router-dom";
import { GitBranch } from "lucide-react";
import { Logo } from "./Logo";

const COLUMNS = [
  {
    title: "Product",
    links: [
      { to: "/", label: "Overview" },
      { to: "/lab", label: "Investigation Lab" },
      { to: "/architecture", label: "Architecture" },
    ],
  },
  {
    title: "Scenarios",
    links: [
      { to: "/lab/duplicate_transaction", label: "Duplicate transactions" },
      { to: "/lab/incorrect_refund", label: "Incorrect refunds" },
      { to: "/lab/monetary_precision", label: "Monetary precision" },
    ],
  },
  {
    title: "Project",
    links: [
      { to: "/about", label: "About & limitations" },
      { to: "/architecture#phase-2", label: "Phase 2 plan" },
    ],
  },
];

export function SiteFooter() {
  return (
    <footer className="relative mt-24 border-t border-white/8 bg-navy-1000">
      <div className="mx-auto grid max-w-[82rem] gap-12 px-4 py-14 sm:px-6 lg:grid-cols-[1.4fr_1fr_1fr_1fr] lg:px-8">
        <div className="flex flex-col gap-4">
          <Link to="/" className="flex items-center gap-3">
            <Logo />
            <span className="font-display text-base font-semibold text-white">
              RootCause<span className="text-cyan-400"> AI</span>
            </span>
          </Link>
          <p className="max-w-xs text-[0.8125rem] leading-relaxed text-ink-faint">
            Autonomous debugging for financial software. Investigate the discrepancy, generate a
            candidate repair, and prove it against protected tests before anyone ships it.
          </p>
          <p className="text-[0.6875rem] uppercase tracking-[0.16em] text-ink-faint">
            Nebius × NVIDIA AI Hackathon
          </p>
        </div>

        {COLUMNS.map((column) => (
          <div key={column.title} className="flex flex-col gap-3">
            <p className="text-[0.6875rem] font-semibold uppercase tracking-[0.16em] text-ink-faint">
              {column.title}
            </p>
            {column.links.map((link) => (
              <Link
                key={link.to + link.label}
                to={link.to}
                className="text-[0.8125rem] text-ink-muted transition-colors hover:text-cyan-300"
              >
                {link.label}
              </Link>
            ))}
          </div>
        ))}
      </div>

      <div className="border-t border-white/8">
        <div className="mx-auto flex max-w-[82rem] flex-col gap-3 px-4 py-6 text-[0.75rem] text-ink-faint sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
          <p>
            Phase 1 preview · demonstration data · synthetic transactions only. Not a production
            financial system.
          </p>
          <div className="flex items-center gap-4">
            <span className="inline-flex items-center gap-1.5">
              <GitBranch className="h-3.5 w-3.5" />
              StarbabyEsther/ROOT-CAUSE-AI
            </span>
            <span>MIT licensed</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

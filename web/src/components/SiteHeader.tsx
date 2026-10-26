import { useEffect, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { Menu, X, ArrowUpRight } from "lucide-react";
import { Logo, Wordmark } from "./Logo";
import { ButtonLink } from "./Button";
import { cn } from "../lib/cn";

const NAV = [
  { to: "/", label: "Overview", end: true },
  { to: "/lab", label: "Investigation Lab" },
  { to: "/architecture", label: "Architecture" },
  { to: "/about", label: "About" },
];

export function SiteHeader() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => setOpen(false), [location.pathname]);

  return (
    <header className="fixed inset-x-0 top-0 z-50">
      <div className="mx-auto max-w-[82rem] px-4 sm:px-6 lg:px-8">
        <div
          className={cn(
            "mt-3 flex h-[4.25rem] items-center justify-between rounded-2xl border px-4 transition-all duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] sm:px-5",
            scrolled || open
              ? "border-white/10 bg-navy-950/80 shadow-[0_24px_60px_-32px_rgba(3,7,15,0.95)] backdrop-blur-xl"
              : "border-transparent bg-transparent",
          )}
        >
          <Link to="/" className="flex items-center gap-3 rounded-xl" aria-label="RootCause AI home">
            <Logo />
            <Wordmark />
          </Link>

          <nav className="hidden items-center gap-1 md:flex" aria-label="Primary">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  cn(
                    "relative rounded-full px-3.5 py-2 text-[0.8125rem] font-medium transition-colors duration-300",
                    isActive ? "text-white" : "text-ink-muted hover:text-white",
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    {isActive && (
                      <span className="absolute inset-0 rounded-full border border-white/10 bg-white/[0.05]" />
                    )}
                    <span className="relative">{item.label}</span>
                  </>
                )}
              </NavLink>
            ))}
          </nav>

          <div className="hidden items-center gap-2.5 md:flex">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-cyan-400/25 bg-cyan-400/[0.07] px-2.5 py-1 text-[0.625rem] font-semibold uppercase tracking-[0.14em] text-cyan-300">
              <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
              Replay demo
            </span>
            <ButtonLink to="/lab" size="sm" className="pr-3">
              Open lab
              <ArrowUpRight className="h-3.5 w-3.5" />
            </ButtonLink>
          </div>

          <button
            type="button"
            onClick={() => setOpen((value) => !value)}
            className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 text-ink md:hidden"
            aria-expanded={open}
            aria-label={open ? "Close navigation" : "Open navigation"}
          >
            {open ? <X className="h-4.5 w-4.5" /> : <Menu className="h-4.5 w-4.5" />}
          </button>
        </div>

        {open && (
          <div className="mt-2 overflow-hidden rounded-2xl border border-white/10 bg-navy-950/95 p-2 backdrop-blur-xl md:hidden">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  cn(
                    "block rounded-xl px-4 py-3 text-sm font-medium",
                    isActive ? "bg-white/[0.06] text-white" : "text-ink-muted",
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
            <div className="p-2">
              <ButtonLink to="/lab" className="w-full">
                Open investigation lab
              </ButtonLink>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}

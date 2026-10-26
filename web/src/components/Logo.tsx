import { cn } from "../lib/cn";

export function Logo({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 40 40" role="img" aria-label="RootCause AI" className={cn("h-9 w-9", className)}>
      <defs>
        <linearGradient id="rc-mark" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#22D3EE" />
          <stop offset="100%" stopColor="#2E6BFF" />
        </linearGradient>
      </defs>
      <rect x="0.75" y="0.75" width="38.5" height="38.5" rx="11" fill="#08111F" stroke="rgba(255,255,255,0.10)" />
      <path
        d="M20 8.5l8.6 4.9v7.4c0 4.9-3.5 8.1-8.6 9.4-5.1-1.3-8.6-4.5-8.6-9.4v-7.4L20 8.5z"
        fill="none"
        stroke="url(#rc-mark)"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
      <circle cx="20" cy="17.6" r="3" fill="url(#rc-mark)" />
      <path d="M20 20.6v7.2" stroke="url(#rc-mark)" strokeWidth="1.7" strokeLinecap="round" />
      <path d="M15.4 26.4h9.2" stroke="url(#rc-mark)" strokeWidth="1.7" strokeLinecap="round" opacity="0.6" />
    </svg>
  );
}

export function Wordmark({ compact = false }: { compact?: boolean }) {
  return (
    <span className="flex items-baseline gap-2">
      <span className="font-display text-[1.0625rem] font-semibold tracking-[-0.02em] text-white">
        RootCause<span className="text-cyan-400"> AI</span>
      </span>
      {!compact && (
        <span className="hidden text-[0.625rem] font-semibold uppercase tracking-[0.18em] text-ink-faint sm:inline">
          Financial reliability
        </span>
      )}
    </span>
  );
}

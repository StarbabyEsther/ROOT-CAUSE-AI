import type { ReactNode } from "react";
import { cn } from "../lib/cn";

const tones = {
  cyan: "border-cyan-400/30 bg-cyan-400/10 text-cyan-300",
  blue: "border-blue-400/30 bg-blue-500/12 text-blue-300",
  mint: "border-mint-400/30 bg-mint-400/10 text-mint-400",
  amber: "border-amber-400/30 bg-amber-400/10 text-amber-400",
  rose: "border-rose-400/30 bg-rose-400/10 text-rose-400",
  neutral: "border-white/12 bg-white/[0.04] text-ink-muted",
} as const;

export function Badge({
  children,
  tone = "neutral",
  className,
  dot = false,
}: {
  children: ReactNode;
  tone?: keyof typeof tones;
  className?: string;
  dot?: boolean;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[0.6875rem] font-medium tracking-[0.02em]",
        tones[tone],
        className,
      )}
    >
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
      {children}
    </span>
  );
}

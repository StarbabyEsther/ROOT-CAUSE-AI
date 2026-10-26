import { Link } from "react-router-dom";
import type { ComponentPropsWithoutRef, ReactNode } from "react";
import { cn } from "../lib/cn";

const variants = {
  primary:
    "bg-blue-500 text-white shadow-[0_10px_30px_-12px_rgba(46,107,255,0.9)] hover:bg-blue-400 hover:shadow-[0_16px_40px_-14px_rgba(46,107,255,0.95)]",
  secondary:
    "border border-white/12 bg-white/[0.03] text-ink hover:border-cyan-400/45 hover:bg-white/[0.06] hover:text-white",
  ghost: "text-ink-muted hover:text-white",
  cyan: "bg-cyan-400/12 text-cyan-300 border border-cyan-400/35 hover:bg-cyan-400/20 hover:text-cyan-200",
} as const;

const sizes = {
  sm: "h-9 px-3.5 text-[0.8125rem]",
  md: "h-11 px-5 text-sm",
  lg: "h-12 px-6 text-[0.9375rem]",
} as const;

type Variant = keyof typeof variants;
type Size = keyof typeof sizes;

const base =
  "inline-flex items-center justify-center gap-2 rounded-full font-medium transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] disabled:pointer-events-none disabled:opacity-45";

export function ButtonLink({
  to,
  variant = "primary",
  size = "md",
  className,
  children,
  external,
  ...rest
}: {
  to: string;
  variant?: Variant;
  size?: Size;
  className?: string;
  children: ReactNode;
  external?: boolean;
} & Omit<ComponentPropsWithoutRef<"a">, "href" | "children" | "className">) {
  if (external) {
    return (
      <a href={to} className={cn(base, variants[variant], sizes[size], className)} {...rest}>
        {children}
      </a>
    );
  }
  return (
    <Link to={to} className={cn(base, variants[variant], sizes[size], className)}>
      {children}
    </Link>
  );
}

export function Button({
  variant = "primary",
  size = "md",
  className,
  children,
  ...rest
}: {
  variant?: Variant;
  size?: Size;
} & ComponentPropsWithoutRef<"button">) {
  return (
    <button className={cn(base, variants[variant], sizes[size], className)} {...rest}>
      {children}
    </button>
  );
}

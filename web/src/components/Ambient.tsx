import { cn } from "../lib/cn";

/** Layered radial light + engineering grid used behind page sections. */
export function Ambient({ className }: { className?: string }) {
  return (
    <div aria-hidden className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)}>
      <div className="grid-field absolute inset-0 opacity-[0.55] [mask-image:radial-gradient(ellipse_70%_60%_at_50%_0%,black,transparent_78%)]" />
      <div className="animate-drift absolute -top-[28rem] left-1/2 h-[46rem] w-[64rem] -translate-x-1/2 rounded-full bg-[radial-gradient(ellipse_at_center,rgba(46,107,255,0.28),rgba(34,211,238,0.10)_45%,transparent_72%)] blur-[2px]" />
      <div className="absolute -right-40 top-40 h-[30rem] w-[30rem] rounded-full bg-[radial-gradient(circle,rgba(34,211,238,0.13),transparent_68%)]" />
      <div className="absolute -left-52 top-[34rem] h-[34rem] w-[34rem] rounded-full bg-[radial-gradient(circle,rgba(46,107,255,0.12),transparent_70%)]" />
    </div>
  );
}

export function SectionRule() {
  return (
    <div aria-hidden className="relative h-px w-full">
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/12 to-transparent" />
      <div className="absolute left-1/2 top-0 h-px w-40 -translate-x-1/2 bg-gradient-to-r from-transparent via-cyan-400/70 to-transparent" />
    </div>
  );
}

import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { Ambient } from "./Ambient";

export function PageHero({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string;
  title: ReactNode;
  description: ReactNode;
  children?: ReactNode;
}) {
  return (
    <section className="relative overflow-hidden pb-10 pt-28 sm:pt-32 lg:pb-14 lg:pt-36">
      <Ambient className="opacity-80" />
      <div className="relative mx-auto max-w-[82rem] px-4 sm:px-6 lg:px-8">
        <motion.p
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
          className="eyebrow flex items-center gap-2"
        >
          <span className="h-1 w-1 rounded-full bg-cyan-400 shadow-[0_0_12px_2px_rgba(34,211,238,0.6)]" />
          {eyebrow}
        </motion.p>
        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.05, ease: [0.22, 1, 0.36, 1] }}
          className="mt-4 max-w-3xl text-[clamp(2rem,4.4vw,3.25rem)] leading-[1.06] tracking-[-0.04em]"
        >
          {title}
        </motion.h1>
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.12 }}
          className="mt-5 max-w-2xl text-[0.9375rem] leading-relaxed text-ink-muted"
        >
          {description}
        </motion.div>
        {children && <div className="mt-7">{children}</div>}
      </div>
    </section>
  );
}

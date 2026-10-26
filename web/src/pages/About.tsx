import { motion } from "framer-motion";
import { ArrowRight, CircleCheck, CircleDashed, GitBranch, GraduationCap, ListChecks } from "lucide-react";
import { PageHero } from "../components/PageHero";
import { usePageTitle } from "../lib/usePageTitle";
import { SectionHeading } from "../components/SectionHeading";
import { SectionRule } from "../components/Ambient";
import { Badge } from "../components/Badge";
import { ButtonLink } from "../components/Button";
import { TOTAL_TESTS } from "../data/scenarios";

const REAL = [
  "Financial totals, expected values and discrepancies — computed by financial_investigator.py against the real records.",
  `Test names and outcomes — ${TOTAL_TESTS} assertions produced by executing the repository's own test files.`,
  "AST validation result — the project's patch_validator.py accepted each reference repair and rejected a malformed control patch.",
  "Captured unittest stdout, including the assertion messages that show the exact wrong values.",
  "Source code shown in the diff is the committed source file.",
];

const ILLUSTRATIVE = [
  "Diagnosis prose — written by hand. NVIDIA Nemotron is integrated in the backend but is not called by this frontend.",
  "The candidate patch is a hand-written reference repair, not a model proposal.",
  "Stage timings are compressed for demonstration; a live run takes seconds to minutes.",
  "Verification executed on local CPython, not inside a Nebius sandbox.",
  "There is no authentication, persistence or multi-user state in Phase 1.",
];

const ROADMAP = [
  {
    status: "done",
    title: "Phase 1 — static frontend",
    body: "Design system, marketing site, investigation lab, animated pipeline, diff viewer, verification dashboard. Replay data only.",
  },
  {
    status: "next",
    title: "Phase 2 — FastAPI adapter",
    body: "Thin service importing workflow.run_workflow, normalising the three report shapes, redacting logs, streaming stage events. Requires approval.",
  },
  {
    status: "later",
    title: "Phase 3 — live wiring & deploy",
    body: "Real investigations against Nebius, credential management on the host, public deployment. Requires approval.",
  },
];

export default function About() {
  usePageTitle("About & limitations");

  return (
    <div className="pb-24">
      <PageHero
        eyebrow="About"
        title={
          <>
            Built to be checkable,
            <span className="text-ink-faint"> not to look clever.</span>
          </>
        }
        description="RootCause AI was built for the Nebius × NVIDIA AI Hackathon in the Coding & Agentic Engineering track. This page states plainly what the demonstration proves and what it does not."
      >
        <div className="flex flex-wrap gap-2">
          <Badge tone="cyan">Nebius × NVIDIA AI Hackathon</Badge>
          <Badge tone="neutral">Coding &amp; Agentic Engineering</Badge>
          <Badge tone="neutral">MIT licensed</Badge>
        </div>
      </PageHero>

      <div className="mx-auto max-w-[82rem] space-y-20 px-4 sm:px-6 lg:px-8">
        <section>
          <SectionHeading
            eyebrow="Demonstration integrity"
            title="Two columns. No blurring between them."
            description="An interface that fabricates a verification result would be worse than no interface at all, so every panel in this build is traceable to one of these lists."
          />
          <div className="mt-8 grid gap-4 lg:grid-cols-2">
            <div className="card p-5">
              <p className="flex items-center gap-2 text-[0.625rem] font-semibold uppercase tracking-[0.16em] text-mint-400">
                <CircleCheck className="h-3.5 w-3.5" />
                Measured / real
              </p>
              <ul className="mt-4 space-y-3">
                {REAL.map((item) => (
                  <li key={item} className="flex items-start gap-2.5 text-[0.8125rem] leading-relaxed text-ink-muted">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-mint-400" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="card p-5">
              <p className="flex items-center gap-2 text-[0.625rem] font-semibold uppercase tracking-[0.16em] text-amber-400">
                <CircleDashed className="h-3.5 w-3.5" />
                Illustrative / not executed
              </p>
              <ul className="mt-4 space-y-3">
                {ILLUSTRATIVE.map((item) => (
                  <li key={item} className="flex items-start gap-2.5 text-[0.8125rem] leading-relaxed text-ink-muted">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-400" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        <div>
          <SectionRule />
        </div>

        <section className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <SectionHeading
              eyebrow="Roadmap"
              title="What is done, and what is waiting."
              description="Phase 1 stops deliberately at the boundary of the backend. Nothing beyond it is built or deployed without explicit approval."
            />
            <div className="mt-7 space-y-3">
              {ROADMAP.map((item) => (
                <div key={item.title} className="flex gap-3 rounded-xl border border-white/8 bg-white/[0.02] p-4">
                  <span
                    className={`mt-1 h-2 w-2 shrink-0 rounded-full ${
                      item.status === "done"
                        ? "bg-mint-400"
                        : item.status === "next"
                          ? "bg-cyan-400"
                          : "bg-white/20"
                    }`}
                  />
                  <div>
                    <p className="text-[0.8125rem] font-medium text-white">{item.title}</p>
                    <p className="mt-1 text-[0.75rem] leading-relaxed text-ink-muted">{item.body}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <SectionHeading
              eyebrow="Limitations"
              title="Known limits of the underlying prototype."
              description="These are inherited from the original project and stated in its technical documentation."
            />
            <ul className="mt-7 space-y-2.5">
              {[
                "Demonstration scenarios use synthetic financial data only.",
                "Repair verification is limited to the supplied regression tests.",
                "Nemotron may generate invalid or unsuccessful patches; the loop allows two attempts.",
                "Nebius Sandbox execution depends on authentication and execution policy.",
                "AST validation alone is not a complete security boundary.",
                "The prototype is not suitable for processing real financial transactions.",
              ].map((item) => (
                <li key={item} className="flex items-start gap-2.5 text-[0.8125rem] leading-relaxed text-ink-muted">
                  <ListChecks className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ink-faint" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </section>

        <div>
          <SectionRule />
        </div>

        <section className="grid gap-4 md:grid-cols-3">
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.45 }}
            className="card p-5 md:col-span-2"
          >
            <p className="flex items-center gap-2 text-[0.625rem] font-semibold uppercase tracking-[0.16em] text-cyan-300">
              <GraduationCap className="h-3.5 w-3.5" />
              Team
            </p>
            <h3 className="mt-3 text-[1.125rem]">Esther &amp; Juliana</h3>
            <p className="mt-2 text-[0.8125rem] leading-relaxed text-ink-muted">
              Developed collaboratively for the Nebius × NVIDIA AI Hackathon, Coding &amp; Agentic
              Engineering track. The investigation engine, repair agent and sandbox verification were
              built as a team; this Phase 1 frontend is an additional layer that leaves that work
              intact.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              {["Python", "NVIDIA Nemotron", "Nebius Sandboxes", "Streamlit", "React", "TypeScript"].map(
                (tag) => (
                  <span
                    key={tag}
                    className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[0.6875rem] text-ink-muted"
                  >
                    {tag}
                  </span>
                ),
              )}
            </div>
          </motion.div>

          <div className="card flex flex-col justify-between p-5">
            <div>
              <p className="flex items-center gap-2 text-[0.625rem] font-semibold uppercase tracking-[0.16em] text-ink-faint">
                <GitBranch className="h-3.5 w-3.5" />
                Repository
              </p>
              <p className="mt-3 font-mono text-[0.75rem] text-ink">StarbabyEsther/ROOT-CAUSE-AI</p>
              <p className="mt-2 text-[0.6875rem] leading-relaxed text-ink-muted">
                Backend, tests and the original Streamlit interface remain exactly as committed. This
                frontend lives in <code className="font-mono text-[0.6875rem] text-cyan-300">web/</code>.
              </p>
            </div>
            <ButtonLink to="/architecture" variant="secondary" size="sm" className="mt-4">
              Review the wiring
              <ArrowRight className="h-3.5 w-3.5" />
            </ButtonLink>
          </div>
        </section>

        <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-white/8 bg-white/[0.02] p-6">
          <p className="max-w-md text-[0.8125rem] leading-relaxed text-ink-muted">
            Every claim on this site should be reproducible. Start with a scenario and inspect the
            evidence panels.
          </p>
          <ButtonLink to="/lab">
            Open the investigation lab
            <ArrowRight className="h-4 w-4" />
          </ButtonLink>
        </div>
      </div>
    </div>
  );
}

import { motion } from "framer-motion";
import {
  ArrowRight,
  Binary,
  BrainCircuit,
  Cpu,
  FileCode2,
  FlaskConical,
  ShieldCheck,
  Sparkles,
  Terminal,
} from "lucide-react";
import { Ambient, SectionRule } from "../components/Ambient";
import { ButtonLink } from "../components/Button";
import { SectionHeading } from "../components/SectionHeading";
import { HeroVisual } from "../components/HeroVisual";
import { Pipeline } from "../components/Pipeline";
import { ScenarioCard } from "../components/ScenarioCard";
import { CodeCompare } from "../components/CodeCompare";
import { Badge } from "../components/Badge";
import { usePageTitle } from "../lib/usePageTitle";
import { SCENARIOS, TOTAL_TESTS } from "../data/scenarios";
import { RUNS } from "../data/runs";

const STATS = [
  { value: "3", label: "financial bug classes", hint: "duplicates · refunds · precision" },
  { value: String(TOTAL_TESTS), label: "protected regression tests", hint: "6 + 7 + 5, scenario-scoped" },
  { value: "4", label: "stage pipeline", hint: "investigate → verify" },
  { value: "2×", label: "sandbox executions", hint: "baseline and candidate" },
];

const STACK = [
  {
    icon: BrainCircuit,
    title: "NVIDIA Nemotron",
    body: "Reads the discrepancy report plus the source file and returns a structured JSON diagnosis. No free-form prose is trusted downstream.",
    tag: "Reasoning",
  },
  {
    icon: Cpu,
    title: "Nebius Token Factory",
    body: "OpenAI-compatible inference endpoint. Model output is parsed and schema-validated before anything else touches it.",
    tag: "Inference",
  },
  {
    icon: FlaskConical,
    title: "Nebius Sandboxes",
    body: "A disposable environment executes the buggy file and the candidate repair against identical protected tests, twice per run.",
    tag: "Evidence",
  },
  {
    icon: ShieldCheck,
    title: "AST structural gate",
    body: "The candidate patch must be exactly one function, with an unchanged signature, no decorators and no default arguments.",
    tag: "Guardrail",
  },
];

const DUPLICATE_RUN = RUNS.duplicate_transaction;
const EVIDENCE_ROWS = [
  ...DUPLICATE_RUN.verification.tests.filter((test) => test.baseline === "fail").slice(0, 2),
  ...DUPLICATE_RUN.verification.tests.filter((test) => test.baseline === "pass").slice(0, 2),
].map((test) => ({
  name: test.name,
  base: test.baseline === "fail" ? "FAIL" : "PASS",
  next: test.reference === "pass" ? "PASS" : "FAIL",
}));

export default function Home() {
  usePageTitle();

  return (
    <div className="relative">
      {/* ---------------------------------------------------------------- hero */}
      <section className="relative overflow-hidden pb-16 pt-28 sm:pt-32 lg:pb-24 lg:pt-40">
        <Ambient />
        <div className="relative mx-auto grid max-w-[82rem] items-center gap-14 px-4 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:gap-10 lg:px-8">
          <div>
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] py-1 pl-1.5 pr-3.5"
            >
              <span className="inline-flex items-center gap-1.5 rounded-full bg-cyan-400/12 px-2 py-0.5 text-[0.5625rem] font-semibold uppercase tracking-[0.14em] text-cyan-300">
                <span className="h-1 w-1 rounded-full bg-cyan-400" />
                Phase 1
              </span>
              <span className="text-[0.6875rem] text-ink-muted">
                Autonomous financial software debugging
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.06, ease: [0.22, 1, 0.36, 1] }}
              className="mt-6 text-[clamp(2.4rem,5.6vw,4.15rem)] leading-[1.03] tracking-[-0.045em]"
            >
              Debug the code
              <br />
              that moves <span className="text-gradient">money.</span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.14 }}
              className="mt-6 max-w-[34rem] text-[0.9375rem] leading-relaxed text-ink-muted sm:text-base"
            >
              RootCause AI re-totals the ledger independently, diagnoses the defect with NVIDIA
              Nemotron, generates a minimal Python repair, and then proves it against protected
              regression tests inside a disposable Nebius sandbox. Nothing is reported as fixed until
              the tests agree.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.22 }}
              className="mt-8 flex flex-wrap items-center gap-3"
            >
              <ButtonLink to="/lab" size="lg">
                Open investigation lab
                <ArrowRight className="h-4 w-4" />
              </ButtonLink>
              <ButtonLink to="/architecture" variant="secondary" size="lg">
                See the architecture
              </ButtonLink>
            </motion.div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.4 }}
              className="mt-8 flex flex-wrap items-center gap-x-5 gap-y-2 text-[0.6875rem] text-ink-faint"
            >
              {["Deterministic investigation", "AST-gated patches", "Sandbox-verified repairs"].map(
                (item) => (
                  <span key={item} className="inline-flex items-center gap-1.5">
                    <Sparkles className="h-3 w-3 text-cyan-400/70" />
                    {item}
                  </span>
                ),
              )}
            </motion.div>
          </div>

          <HeroVisual />
        </div>

        <div className="relative mx-auto mt-16 max-w-[82rem] px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-white/8 bg-white/[0.06] lg:grid-cols-4">
            {STATS.map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.5 + index * 0.08 }}
                className="bg-navy-950 px-5 py-5"
              >
                <p className="font-display text-[1.75rem] font-semibold leading-none text-white">
                  {stat.value}
                </p>
                <p className="mt-2 text-[0.75rem] font-medium text-ink">{stat.label}</p>
                <p className="mt-0.5 text-[0.6875rem] text-ink-faint">{stat.hint}</p>
              </motion.div>
            ))}
          </div>
          <p className="mt-3 text-center text-[0.6875rem] text-ink-faint">
            Demonstration data. Figures and test results are produced by the project's real Python
            modules; no model is called in Phase 1.
          </p>
        </div>
      </section>

      {/* ------------------------------------------------------------ pipeline */}
      <section className="relative py-20 lg:py-24">
        <div className="mx-auto max-w-[82rem] px-4 sm:px-6 lg:px-8">
          <SectionHeading
            eyebrow="The loop"
            title={
              <>
                Four stages. Each one leaves an artifact
                <span className="text-ink-faint"> the next one cannot fake.</span>
              </>
            }
            description="A hypothesis is cheap. Every stage in RootCause AI produces evidence the following stage has to consume — which is what keeps a confident-sounding diagnosis from being mistaken for a fix."
          />
          <div className="mt-10">
            <Pipeline />
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-[82rem] px-4 sm:px-6 lg:px-8">
        <SectionRule />
      </div>

      {/* ----------------------------------------------------------- scenarios */}
      <section className="py-20 lg:py-24">
        <div className="mx-auto max-w-[82rem] px-4 sm:px-6 lg:px-8">
          <div className="flex flex-wrap items-end justify-between gap-6">
            <SectionHeading
              eyebrow="Scenario library"
              title="Three ways financial code quietly gets it wrong."
              description="Each scenario ships with its own protected regression suite. Pick one and watch the pipeline run end to end."
            />
            <ButtonLink to="/lab" variant="secondary" size="md" className="shrink-0">
              Compare all scenarios
              <ArrowRight className="h-3.5 w-3.5" />
            </ButtonLink>
          </div>

          <div className="mt-10 grid gap-4 md:grid-cols-3">
            {SCENARIOS.map((scenario, index) => (
              <ScenarioCard key={scenario.id} scenario={scenario} index={index} />
            ))}
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------ evidence */}
      <section className="relative overflow-hidden py-20 lg:py-24">
        <div
          aria-hidden
          className="absolute left-1/2 top-0 h-[28rem] w-[54rem] -translate-x-1/2 rounded-full bg-[radial-gradient(ellipse_at_center,rgba(34,211,238,0.10),transparent_70%)]"
        />
        <div className="relative mx-auto grid max-w-[82rem] items-center gap-12 px-4 sm:px-6 lg:grid-cols-2 lg:px-8">
          <div>
            <SectionHeading
              eyebrow="Evidence over assertion"
              title={
                <>
                  A diagnosis is a hypothesis.
                  <br />
                  <span className="text-gradient-cyan">Tests are evidence.</span>
                </>
              }
              description="The candidate repair is never applied to the repository. It is written into a disposable copy, executed against the same protected tests the buggy file is executed against, and only then reported."
            />
            <ul className="mt-7 space-y-3">
              {[
                "Baseline and candidate run in separate, disposable sandboxes",
                "Records, imports and helper functions are verified unchanged by AST comparison",
                "A two-function or re-signed patch is rejected before it can execute",
                "Passing is reported as bounded evidence, never as proof of correctness",
              ].map((item) => (
                <li key={item} className="flex items-start gap-2.5 text-[0.8125rem] leading-relaxed text-ink-muted">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-400/80" />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.6 }}
            className="card overflow-hidden"
          >
            <div className="flex items-center justify-between border-b border-white/8 px-4 py-3">
              <div className="flex items-center gap-2">
                <Terminal className="h-3.5 w-3.5 text-cyan-400" />
                <span className="font-mono text-[0.6875rem] text-ink-muted">
                  {RUNS.duplicate_transaction.verification.tests.length} tests · duplicate_transaction
                </span>
              </div>
              <Badge tone="mint" dot>
                {DUPLICATE_RUN.verification.reference.passed} /{" "}
                {DUPLICATE_RUN.verification.reference.ran} pass
              </Badge>
            </div>
            <div className="divide-y divide-white/5">
              {EVIDENCE_ROWS.map((row) => (
                <div key={row.name} className="flex items-center justify-between gap-3 px-4 py-2.5">
                  <span className="truncate font-mono text-[0.6875rem] text-ink-muted">{row.name}</span>
                  <span className="flex items-center gap-2 font-mono text-[0.5625rem]">
                    <span className={row.base === "FAIL" ? "text-rose-400" : "text-ink-faint"}>{row.base}</span>
                    <ArrowRight className="h-2.5 w-2.5 text-ink-faint" />
                    <span className="text-mint-400">{row.next}</span>
                  </span>
                </div>
              ))}
            </div>
            <div className="border-t border-white/8 bg-navy-950/50 px-4 py-2.5">
              <p className="font-mono text-[0.625rem] text-ink-faint">
                baseline: {DUPLICATE_RUN.verification.baseline.failed} failing → candidate:{" "}
                {DUPLICATE_RUN.verification.reference.failed} failing
              </p>
            </div>
          </motion.div>
        </div>
      </section>

      <div className="mx-auto max-w-[82rem] px-4 sm:px-6 lg:px-8">
        <SectionRule />
      </div>

      {/* ---------------------------------------------------------------- diff */}
      <section className="py-20 lg:py-24">
        <div className="mx-auto max-w-[82rem] px-4 sm:px-6 lg:px-8">
          <SectionHeading
            eyebrow="Read the repair"
            title="A minimal diff, in the one function allowed to change."
            description="This is the reference repair for the duplicate-transaction scenario, shown against the committed source. The generated patch is a proposal — the repository is never rewritten."
          />
          <div className="mt-9">
            <CodeCompare code={RUNS.duplicate_transaction.code} />
          </div>
        </div>
      </section>

      {/* --------------------------------------------------------------- stack */}
      <section className="relative py-20 lg:py-24">
        <div className="mx-auto max-w-[82rem] px-4 sm:px-6 lg:px-8">
          <SectionHeading
            eyebrow="Technology"
            title="Two models of trust, working together."
            description="Nemotron reasons. The sandbox decides. Everything between them is schema validation and structural checks."
          />
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {STACK.map((item, index) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.45, delay: index * 0.07 }}
                className="card card-hover flex flex-col gap-3 p-4"
              >
                <div className="flex items-center justify-between">
                  <span className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 bg-white/[0.04] text-cyan-300">
                    <item.icon className="h-4 w-4" />
                  </span>
                  <span className="text-[0.5625rem] uppercase tracking-[0.14em] text-ink-faint">
                    {item.tag}
                  </span>
                </div>
                <h3 className="text-[0.9375rem] font-semibold text-white">{item.title}</h3>
                <p className="text-[0.75rem] leading-relaxed text-ink-muted">{item.body}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- honesty */}
      <section className="py-16 lg:py-20">
        <div className="mx-auto max-w-[82rem] px-4 sm:px-6 lg:px-8">
          <div className="card grid gap-8 p-6 lg:grid-cols-2 lg:p-8">
            <div>
              <p className="eyebrow flex items-center gap-2">
                <Binary className="h-3.5 w-3.5" />
                Demonstration integrity
              </p>
              <h2 className="mt-3 text-[1.5rem] leading-tight">
                What this preview is, and what it refuses to claim.
              </h2>
              <p className="mt-3 text-[0.8125rem] leading-relaxed text-ink-muted">
                Phase 1 is a static frontend. It replays recorded evidence rather than pretending to
                run an agent in your browser — because an interface that fabricates a verification
                result is worse than no interface at all.
              </p>
              <ButtonLink to="/about" variant="secondary" size="sm" className="mt-5">
                Read the limitations
                <ArrowRight className="h-3.5 w-3.5" />
              </ButtonLink>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-mint-400/20 bg-mint-400/[0.05] p-4">
                <p className="text-[0.625rem] font-semibold uppercase tracking-[0.14em] text-mint-400">
                  Measured
                </p>
                <ul className="mt-2 space-y-1.5 text-[0.75rem] leading-relaxed text-ink-muted">
                  <li>Financial totals and discrepancies</li>
                  <li>Regression test names and outcomes</li>
                  <li>AST validator pass and rejection</li>
                  <li>Captured unittest output</li>
                </ul>
              </div>
              <div className="rounded-xl border border-amber-400/20 bg-amber-400/[0.05] p-4">
                <p className="text-[0.625rem] font-semibold uppercase tracking-[0.14em] text-amber-400">
                  Illustrative
                </p>
                <ul className="mt-2 space-y-1.5 text-[0.75rem] leading-relaxed text-ink-muted">
                  <li>Diagnosis wording — no model call</li>
                  <li>Candidate patch — hand-written reference</li>
                  <li>Timing — compressed for demonstration</li>
                  <li>Sandbox — tests ran on local CPython</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------------------- cta */}
      <section className="relative overflow-hidden py-20 lg:py-28">
        <div
          aria-hidden
          className="absolute inset-x-0 bottom-0 h-72 bg-[radial-gradient(ellipse_at_50%_100%,rgba(46,107,255,0.22),transparent_70%)]"
        />
        <div className="relative mx-auto max-w-[46rem] px-4 text-center sm:px-6">
          <p className="eyebrow">Investigation lab</p>
          <h2 className="mt-3 text-[clamp(1.9rem,4vw,2.9rem)] leading-[1.08]">
            Bring a broken ledger.
            <br />
            <span className="text-gradient">Leave with evidence.</span>
          </h2>
          <p className="mx-auto mt-4 max-w-lg text-[0.875rem] leading-relaxed text-ink-muted">
            Slide through the four stages, read the diff, and check the test matrix yourself. Every
            figure is inspectable and every claim is labelled.
          </p>
          <div className="mt-7 flex flex-wrap items-center justify-center gap-3">
            <ButtonLink to="/lab" size="lg">
              <FileCode2 className="h-4 w-4" />
              Start an investigation
            </ButtonLink>
            <ButtonLink to="/architecture" variant="ghost" size="lg">
              How it is wired
              <ArrowRight className="h-4 w-4" />
            </ButtonLink>
          </div>
        </div>
      </section>
    </div>
  );
}

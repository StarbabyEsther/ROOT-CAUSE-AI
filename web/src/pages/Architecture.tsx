import { motion } from "framer-motion";
import {
  ArrowRight,
  Boxes,
  Database,
  FileJson2,
  GitBranch,
  HardDrive,
  Layers,
  Link2,
  Lock,
  ServerCog,
  ShieldCheck,
  Workflow,
} from "lucide-react";
import { PageHero } from "../components/PageHero";
import { usePageTitle } from "../lib/usePageTitle";
import { Pipeline } from "../components/Pipeline";
import { SectionHeading } from "../components/SectionHeading";
import { SectionRule } from "../components/Ambient";
import { Badge } from "../components/Badge";
import { ButtonLink } from "../components/Button";

const MODULES = [
  ["scenario_registry.py", "Maps each scenario id to its records, calculator and source file."],
  ["financial_investigator.py", "Deterministic re-total and discrepancy classification. No model involved."],
  ["nemotron_client.py", "Nebius Token Factory client for the structured diagnosis."],
  ["patch_generator.py", "Requests a candidate repair and validates its shape."],
  ["patch_validator.py", "AST gate: one function, same signature, no decorators or defaults."],
  ["sandbox_verifier.py", "Runs baseline and candidate in disposable Nebius sandboxes."],
  ["prepare_sandbox_tests.py", "Splices the candidate into a copy and builds the regression bundle."],
  ["workflow.py", "Single orchestration seam: run_workflow(scenario_id) → result dict."],
  ["streamlit_app.py", "The existing deployed interface. Preserved unchanged."],
];

const ARTIFACTS = [
  ["financial_report.json", "Independent totals, discrepancy, classification"],
  ["proposed_patch.json", "root_cause · explanation · target_file · proposed_code"],
  ["sandbox_verification_report.json", "verdict · baseline_failed · final_passed · logs"],
  ["verification_bundle/", "Disposable copy of the source plus the protected tests"],
];

export default function Architecture() {
  usePageTitle("Architecture");

  return (
    <div className="pb-24">
      <PageHero
        eyebrow="Architecture"
        title={
          <>
            A thin orchestration seam,
            <span className="text-ink-faint"> four honest artifacts.</span>
          </>
        }
        description="RootCause AI is a set of plain Python modules with one reusable entry point. The frontend you are reading is deliberately decoupled from it, so the investigation engine can be trusted to stay exactly as it is."
      >
        <div className="flex flex-wrap gap-2">
          <Badge tone="mint" dot>
            Phase 1 · frontend delivered
          </Badge>
          <Badge tone="cyan">Python backend unmodified</Badge>
          <Badge tone="neutral">Streamlit deployment preserved</Badge>
        </div>
      </PageHero>

      <div className="mx-auto max-w-[82rem] space-y-20 px-4 sm:px-6 lg:px-8">
        <section>
          <SectionHeading
            eyebrow="Pipeline"
            title="Investigate → diagnose → repair → verify."
            description="Each stage writes an artifact that the next stage must consume. The verdict is only ever produced by the last one."
          />
          <div className="mt-8">
            <Pipeline />
          </div>
        </section>

        <div>
          <SectionRule />
        </div>

        <section className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr]">
          <div>
            <SectionHeading
              eyebrow="Module map"
              title="Where each responsibility lives."
              description="Every module below is pre-existing and untouched by this redesign."
            />
            <div className="mt-7 overflow-hidden rounded-2xl border border-white/8">
              {MODULES.map(([name, role], index) => (
                <div
                  key={name}
                  className={`grid gap-1 px-4 py-3 sm:grid-cols-[13rem_1fr] sm:gap-4 ${
                    index % 2 === 0 ? "bg-white/[0.015]" : ""
                  }`}
                >
                  <code className="font-mono text-[0.6875rem] text-cyan-300">{name}</code>
                  <p className="text-[0.75rem] leading-relaxed text-ink-muted">{role}</p>
                </div>
              ))}
            </div>
          </div>

          <div>
            <SectionHeading
              eyebrow="Artifacts"
              title="State is files, not a database."
              description="Runs communicate through JSON written beside the code — which is what makes the pipeline reproducible and easy to audit."
            />
            <div className="mt-7 space-y-3">
              {ARTIFACTS.map(([name, role]) => (
                <div key={name} className="card flex items-start gap-3 p-4">
                  <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-white/10 bg-white/[0.03] text-cyan-300">
                    <FileJson2 className="h-3.5 w-3.5" />
                  </span>
                  <div>
                    <code className="font-mono text-[0.75rem] text-ink">{name}</code>
                    <p className="mt-1 text-[0.6875rem] leading-relaxed text-ink-muted">{role}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <div>
          <SectionRule />
        </div>

        <section>
          <SectionHeading
            eyebrow="Separation of concerns"
            title="Reasoning and proof are different subsystems."
            description="The model is allowed to propose. Only the sandbox is allowed to conclude."
          />
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {[
              {
                icon: Layers,
                title: "Deterministic investigation",
                body: "The discrepancy is computed by re-totalling the ledger — not by asking a model. Duplicate ids, refund signs and float drift are classified with arithmetic.",
                tag: "No model",
              },
              {
                icon: ServerCog,
                title: "Model proposes",
                body: "Nemotron returns strict JSON. It cannot mark its own work as verified, and the prompts explicitly forbid claiming a fix without test evidence.",
                tag: "Bounded",
              },
              {
                icon: ShieldCheck,
                title: "Sandbox concludes",
                body: "Baseline and candidate execute in separate disposable environments against the same protected tests. The verdict is derived from exit status and test counts.",
                tag: "Evidence",
              },
            ].map((item) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 14 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.45 }}
                className="card p-5"
              >
                <div className="flex items-center justify-between">
                  <span className="flex h-9 w-9 items-center justify-center rounded-xl border border-cyan-400/25 bg-cyan-400/[0.08] text-cyan-300">
                    <item.icon className="h-4 w-4" />
                  </span>
                  <span className="text-[0.5625rem] uppercase tracking-[0.14em] text-ink-faint">
                    {item.tag}
                  </span>
                </div>
                <h3 className="mt-3 text-[0.9375rem] font-semibold text-white">{item.title}</h3>
                <p className="mt-2 text-[0.75rem] leading-relaxed text-ink-muted">{item.body}</p>
              </motion.div>
            ))}
          </div>
        </section>

        <div>
          <SectionRule />
        </div>

        <section>
          <SectionHeading
            eyebrow="Isolation & safety"
            title="What the guardrails actually enforce."
            description="Structural validation is a real gate, but it is not a complete security boundary — and the project says so."
          />
          <div className="mt-8 grid gap-4 sm:grid-cols-2">
            {[
              ["Single function only", "The candidate patch must parse to exactly one function definition named calculate_total."],
              ["Signature preserved", "Parameter lists are compared with AST dump equality; decorators and default arguments are rejected."],
              ["Records untouched", "All top-level nodes outside the target function must be byte-identical after splicing."],
              ["Disposable execution", "Tests run in remote sandboxes; the working repository is never patched in place."],
              ["Secrets stay server-side", "Inference credentials live in the API process environment, never in a browser bundle."],
              ["Honest limits", "AST validation is not a sandbox. Permission, network and resource policies need review before production use."],
            ].map(([title, body]) => (
              <div key={title} className="rounded-xl border border-white/8 bg-white/[0.02] p-4">
                <p className="flex items-center gap-2 text-[0.8125rem] font-medium text-white">
                  <Lock className="h-3.5 w-3.5 text-cyan-400" />
                  {title}
                </p>
                <p className="mt-1.5 text-[0.75rem] leading-relaxed text-ink-muted">{body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ------------------------------------------------------ phase 2 plan */}
        <section id="phase-2" className="scroll-mt-28">
          <div className="card overflow-hidden">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/8 px-6 py-4">
              <div className="flex items-center gap-2.5">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-blue-400/30 bg-blue-500/10 text-blue-300">
                  <Workflow className="h-4 w-4" />
                </span>
                <div>
                  <p className="text-[0.9375rem] font-medium text-white">Phase 2 — planned, not built</p>
                  <p className="text-[0.6875rem] text-ink-faint">
                    A separate FastAPI adapter; the Python backend stays untouched
                  </p>
                </div>
              </div>
              <Badge tone="amber" dot>
                Awaiting approval
              </Badge>
            </div>

            <div className="grid gap-6 p-6 lg:grid-cols-2">
              <div>
                <p className="text-[0.625rem] font-semibold uppercase tracking-[0.14em] text-ink-faint">
                  Connection plan
                </p>
                <div className="mt-3 space-y-2 font-mono text-[0.6875rem]">
                  {[
                    ["Browser", "React SPA · no credentials"],
                    ["/api/*", "same-origin proxy"],
                    ["FastAPI adapter", "normalises reports, redacts logs"],
                    ["workflow.run_workflow(id)", "imported, never modified"],
                    ["Nebius", "Nemotron + sandboxes"],
                  ].map(([left, right], index) => (
                    <div key={left} className="flex items-center gap-2">
                      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded border border-white/10 font-mono text-[0.5625rem] text-ink-faint">
                        {index + 1}
                      </span>
                      <span className="rounded bg-white/[0.04] px-2 py-1 text-cyan-300">{left}</span>
                      <ArrowRight className="h-3 w-3 shrink-0 text-ink-faint" />
                      <span className="text-ink-muted">{right}</span>
                    </div>
                  ))}
                </div>
                <p className="mt-4 text-[0.75rem] leading-relaxed text-ink-muted">
                  The SPA already ships a typed client for exactly this contract. Switching from
                  recorded evidence to live investigations is a transport change — set{" "}
                  <code className="rounded bg-white/[0.06] px-1 py-0.5 font-mono text-[0.6875rem] text-cyan-300">
                    VITE_API_MODE=live
                  </code>{" "}
                  — not a redesign.
                </p>
              </div>

              <div>
                <p className="text-[0.625rem] font-semibold uppercase tracking-[0.14em] text-ink-faint">
                  Endpoint contract
                </p>
                <div className="mt-3 overflow-hidden rounded-xl border border-white/8">
                  {[
                    ["GET", "/api/health", "mode, sandbox availability"],
                    ["GET", "/api/scenarios", "ids, titles, test counts"],
                    ["POST", "/api/investigations", "start a run → id"],
                    ["GET", "/api/investigations/:id", "normalised result"],
                    ["GET", "/api/investigations/:id/events", "SSE stage progress"],
                  ].map(([method, path, note], index) => (
                    <div
                      key={path}
                      className={`grid grid-cols-[3.2rem_1fr] gap-2 px-3 py-2.5 ${
                        index % 2 === 0 ? "bg-white/[0.015]" : ""
                      }`}
                    >
                      <span className="font-mono text-[0.5625rem] uppercase text-cyan-300">{method}</span>
                      <div>
                        <code className="font-mono text-[0.6875rem] text-ink">{path}</code>
                        <p className="text-[0.625rem] text-ink-faint">{note}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid gap-3 border-t border-white/8 bg-navy-950/40 px-6 py-4 sm:grid-cols-3">
              {[
                { icon: Database, text: "Per-run temp workspace keeps report paths isolated" },
                { icon: HardDrive, text: "Existing Streamlit Cloud deployment keeps serving" },
                { icon: Link2, text: "SSE progress, then polling fallback" },
              ].map((item) => (
                <p key={item.text} className="flex items-start gap-2 text-[0.6875rem] leading-relaxed text-ink-muted">
                  <item.icon className="mt-0.5 h-3.5 w-3.5 shrink-0 text-cyan-400" />
                  {item.text}
                </p>
              ))}
            </div>
          </div>
        </section>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { icon: GitBranch, label: "Branch", value: "arena-website-redesign" },
            { icon: Boxes, label: "Frontend", value: "React 19 · Vite · Tailwind 4" },
            { icon: Lock, label: "Credentials", value: "none in this bundle" },
            { icon: ShieldCheck, label: "Backend", value: "unmodified since c63b5ed" },
          ].map((item) => (
            <div key={item.label} className="rounded-xl border border-white/8 bg-white/[0.02] p-4">
              <item.icon className="h-3.5 w-3.5 text-cyan-400" />
              <p className="mt-2 text-[0.5625rem] uppercase tracking-[0.14em] text-ink-faint">{item.label}</p>
              <p className="mt-0.5 font-mono text-[0.6875rem] text-ink">{item.value}</p>
            </div>
          ))}
        </section>

        <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-white/8 bg-white/[0.02] p-6">
          <p className="max-w-md text-[0.8125rem] leading-relaxed text-ink-muted">
            Read the recorded evidence for yourself before anything is connected.
          </p>
          <ButtonLink to="/lab">
            Open the lab
            <ArrowRight className="h-4 w-4" />
          </ButtonLink>
        </div>
      </div>
    </div>
  );
}

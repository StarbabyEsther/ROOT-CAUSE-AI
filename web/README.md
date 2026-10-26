# RootCause AI — Frontend (Phase 1)

Premium React frontend for **RootCause AI**, an autonomous financial software debugging
assistant. This directory is entirely additive: the Python backend, the regression tests and the
existing Streamlit deployment are **not modified and not required** to run it.

> **Phase 1 scope.** This build is a static, replay-driven demonstration. It does **not** call
> NVIDIA Nemotron and it does **not** execute anything in a Nebius sandbox. Every figure, test
> outcome and validation result shown in the UI is measured data recorded from the project's real
> Python modules — see [Demonstration integrity](#demonstration-integrity). Nothing here is
> presented as a live AI execution.

---

## Quick start

```bash
cd web
npm install
npm run dev          # http://localhost:5173
```

Requirements: Node 20+ (developed on Node 22).

| Script | Purpose |
|---|---|
| `npm run dev` | Vite dev server, bound to `0.0.0.0:5173` |
| `npm run build` | Type-check + production build to `dist/` |
| `npm run preview` | Serve the production build |
| `npm run typecheck` | TypeScript only |
| `npm run smoke` | Render every route in Node (catches runtime errors) |
| `npm run smoke:panels` | Assert the investigation panels contain the measured values |

---

## Routes

| Route | What it is |
|---|---|
| `/` | Landing: hero, four-stage pipeline, scenario library, evidence panel, live code diff, tech stack, demonstration-integrity summary |
| `/lab` | Scenario picker with ledger preview and launch action |
| `/lab/:scenarioId` | The investigation workspace: animated four-stage timeline, financial panel, diagnosis, side-by-side diff, verification dashboard |
| `/architecture` | Module map, artifacts, guardrails, Phase 2 connection plan |
| `/about` | Team, roadmap, and an explicit measured-vs-illustrative breakdown |

Scenario ids: `duplicate_transaction`, `incorrect_refund`, `monetary_precision`.

---

## Architecture

```
web/
├── index.html
├── vite.config.ts            # /api proxy ready for Phase 2 (unused in Phase 1)
├── scripts/ssr-smoke.tsx     # renders every route in Node to catch runtime errors
└── src/
    ├── App.tsx               # routes
    ├── styles/global.css     # design tokens (@theme), base layer, custom utilities
    ├── lib/
    │   ├── contract.ts       # shared result types — mirrors the Python artifacts
    │   ├── api.ts            # transport: replay (Phase 1) | live (Phase 2)
    │   ├── useInvestigation.ts
    │   ├── diff.ts           # LCS line diff with similarity pairing
    │   └── format.ts         # currency, exact-decimal and scientific formatting
    ├── data/
    │   ├── scenarios.ts      # the three scenarios (records copied from the processors)
    │   ├── measured.json     # MEASURED evidence: totals, test outcomes, AST validation
    │   └── runs.ts           # merges measured evidence with clearly-labelled narrative text
    ├── components/           # design primitives + investigation panels
    └── pages/
```

### Design system

Defined once in `src/styles/global.css` under Tailwind v4 `@theme`:

- **Ground:** `navy-1000 → navy-600` (`#03070F` → `#274060`)
- **Primary:** electric blue `#2E6BFF`; **accent:** cyan `#22D3EE`
- **Status:** mint `#34E0C4` (pass) / amber `#F5B547` (caution) / rose `#FB7185` (fail)
- **Type:** Sora (display) · Inter (UI) · JetBrains Mono (code, amounts, ids), self-hosted
- **Motion:** Framer Motion for reveals and stage transitions; CSS keyframes for ambient light.
  Everything respects `prefers-reduced-motion`.

### Transport seam (why Phase 2 will not require a redesign)

`src/lib/api.ts` exposes one function:

```ts
startInvestigation(scenarioId, { onStage, onComplete, onError }): () => void
```

- **replay** (current default): plays recorded evidence on a compressed timeline.
- **live** (already written, unused): `POST /api/investigations`, then an SSE stream on
  `/api/investigations/{id}/events`.

Both modes produce the same `InvestigationResult` from `src/lib/contract.ts`, so components never
learn where the data came from. That contract is the spec the Phase 2 FastAPI adapter must satisfy.

Switching modes is one environment variable — no component changes:

```bash
VITE_API_MODE=live API_PROXY_TARGET=http://127.0.0.1:8000 npm run dev
```

**No credentials ever enter this bundle.** Only `VITE_`-prefixed variables reach the browser, and
none of them is ever a secret. Inference credentials belong to the server-side adapter.

---

## Verification of the demo data

The numbers in `src/data/measured.json` were produced by running the repository's own modules, not
by hand:

| Scenario | Source file | Baseline (buggy) | Reference repair |
|---|---|---|---|
| Duplicate transactions | `transactions.py` | 6 tests, **3 failing** | 6/6 pass |
| Incorrect refunds | `refund_processor.py` | 7 tests, **3 failing** | 7/7 pass |
| Monetary precision | `precision_processor.py` | 5 tests, **4 failing** | 5/5 pass |

Also measured:

- **Financial reports** from `financial_investigator.investigate_transactions()` — e.g. duplicate
  scenario reports `600.0` against an expected `400.00` (discrepancy `200.00`); precision reports
  `0.20000000000000004` against `0.20` (discrepancy `4E-17`).
- **AST gate** from `patch_validator.py` — accepted all three reference repairs and rejected a
  deliberately malformed two-function control patch.
- **Captured stdout** of each unittest run (shown in the collapsible log viewer).

Tests ran on local CPython during Phase 1, **not** in Nebius sandboxes. The UI states this
explicitly in every verification panel.

---

## What is explicitly NOT real

- **Diagnosis prose** — hand-written. No model is invoked.
- **Candidate patches** — hand-written reference repairs, not Nemotron output.
- **Timings** — compressed for demonstration.
- **Sandbox execution** — none. Local CPython only.
- **Auth, persistence, multi-user state** — none.

Each of these is labelled in the interface (`DemoBanner`, the illustrative badge on the diagnosis
panel, and the provenance panel under every investigation).

---

## Smoke test

Renders all routes in Node to catch runtime errors without a browser:

```bash
npm run smoke         # every route renders
npm run smoke:panels  # every investigation panel shows the recorded values
```

---

## Constraints honoured

| Constraint | Status |
|---|---|
| Do not modify the Python backend | No file outside `web/` was touched |
| Do not modify regression tests | Untouched; their output is only *read* |
| Do not touch `main`, `Juliana`, `integration-juliana` | Untouched |
| Preserve the Streamlit deployment | `streamlit_app.py`, `.streamlit/` untouched |
| No credentials introduced or exposed | None present; `.env*` ignored; no `VITE_` secrets |
| Frontend confined to `web/` | Yes |

## Next step (needs approval)

Phase 2 adds `api/` — a FastAPI adapter that imports `workflow.run_workflow` unchanged, normalises
the three inconsistent report shapes, redacts logs, and streams stage events. See `/architecture`
in the running app, or `docs/frontend-architecture-proposal.md` at the repository root.

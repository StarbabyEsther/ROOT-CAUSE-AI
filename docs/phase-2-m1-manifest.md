# M1 Manifest — API Adapter Skeleton

**Scope approved:** M1 only (adapter skeleton + tests). No M2, no deployment, no backend edits.
Status: awaiting confirmation of this file list before any file is created.

---

## 1. Nebius model — inspection result

**I cannot identify the configured model from the repository, because it is not in the repository.**

| Check | Result |
|---|---|
| `NEBIUS_MODEL` value committed to git | **No.** Only the placeholder `NEBIUS_MODEL=your_nemotron_model_here` in `README.md:128` |
| Any hardcoded model identifier (`nvidia/…`, `nemotron-…`) in source | **None** |
| Any `.env`, `secrets.toml`, `.pem`, `.key` ever committed in history | **None** |
| Where the value is actually read | `nemotron_client.py:13` and `patch_generator.py:12`, from the environment at import time; `nemotron_client.py` additionally falls back to Streamlit secrets |

So the live model is whatever is set in your local `.env` and/or the Streamlit Cloud **Secrets**
panel. I have no way to read it, and I did not attempt to probe your deployment.

**Action for you:** quote only the model *name* (e.g. `nvidia/Nemotron-…`) — never the API key.
It does not need to be in the repo; M1 reads it from the environment exactly as the existing
code does, and never echoes it back through the API.

---

## 2. Precision artifacts — safe to ignore

Checked for tracking **before** adding any rule:

| Path | Tracked by git | Exists on disk |
|---|---|---|
| `precision_verification_bundle/` | no | no |
| `precision_verification_report.json` | no | no |
| `precision_proposed_patch.json` | no | no |

None is tracked and none currently exists, so adding ignore patterns **cannot delete or hide
existing evidence**. The patterns only prevent future accidental commits. Existing
`verification_bundle/`, `refund_verification_bundle/` and their reports are untouched — the rules
added are three new lines, and no existing line is removed.

---

## 3. Files to CREATE (all new; nothing overwritten)

### Adapter

| File | Purpose |
|---|---|
| `api/__init__.py` | package marker |
| `api/config.py` | env-driven settings: `LIVE_RUNS_ENABLED`, limits, allowed origins, state dir, workspace root, child command override (tests) |
| `api/contracts.py` | Pydantic models mirroring `web/src/lib/contract.ts` — the single source of truth for the wire format |
| `api/normalise.py` | turns the three inconsistent backend reports into one `InvestigationResult`; parses per-test outcomes from unittest output |
| `api/redact.py` | removes `NEBIUS_API_KEY`, `CONTREE_TOKEN`, and anything matching common key shapes from logs and error text |
| `api/workspace.py` | creates `/tmp/rcai/<job-id>/`, copies only the backend `.py` modules + tests into it, guarantees cleanup |
| `api/jobs.py` | job registry, one-concurrent queue, subprocess launcher, stdout tailing → stage events, result assembly |
| `api/limits.py` | **persistent** limiter in SQLite: 2/IP/hour, 5/IP/day, 30 global/day, 1 concurrent — survives restarts |
| `api/main.py` | FastAPI app + routes + CORS + error mapping |
| `api/requirements-api.txt` | `fastapi`, `uvicorn[standard]`, `pydantic`, `httpx`, `pytest` (additive; root `requirements.txt` untouched) |
| `api/.env.example` | names with empty values only — no secrets |
| `api/README.md` | how to run locally, how to read the limits, what is *not* implemented yet |

### Tests

| File | Covers |
|---|---|
| `api/tests/__init__.py` | package marker |
| `api/tests/conftest.py` | fake child process + fixture repo copy; temp state dir per test |
| `api/tests/test_contract.py` | response models match the TypeScript contract; hidden-field parity |
| `api/tests/test_normalise.py` | all three report shapes, incl. `refund_sign_error` and missing `elapsed_seconds` |
| `api/tests/test_redact.py` | secrets removed from logs, tracebacks and error strings |
| `api/tests/test_limits.py` | per-IP hour/day, global day, restart persistence, concurrent requests cannot overshoot the global cap |
| `api/tests/test_workspace.py` | per-job isolation, only `.py` copied, cleanup on success and on failure |
| `api/tests/test_routes.py` | health/scenarios/404/429, artifact path traversal rejected, no key material in any response body |

### Docs / config touched

| File | Change |
|---|---|
| `.gitignore` (root) | **+3 lines** for the precision artifacts |
| `docs/phase-2-m1-manifest.md` | this file |

---

## 4. Files explicitly NOT modified

- Every root-level `.py`: `workflow.py`, `main.py`, `refund_ai_repair.py`, `precision_ai_repair.py`,
  `sandbox_verifier.py`, `patch_validator.py`, `patch_generator.py`, `nemotron_client.py`,
  `financial_investigator.py`, `scenario_registry.py`, `prepare_sandbox_tests.py`,
  `repair_agent.py`, `repair_verifier.py`, `debug_agent.py`, and the three `*_processor.py` files
- All `test_*.py` regression tests
- `streamlit_app.py`, `streamlit_app_v2.py`, `.streamlit/config.toml`
- `requirements.txt`
- Everything under `web/` (theme work is M3)
- `main`, `Juliana`, `integration-juliana`

---

## 5. Can M1 be completed without changing the repair scripts?

**Yes — and the existing code already has the seams for it.** Six specific reasons:

| Need | Existing capability | Change required |
|---|---|---|
| Run a scenario | `workflow.run_workflow(scenario_id)->dict`, the documented seam | none |
| Isolate each run | `workflow.ROOT = Path(__file__).parent` — probed: resolves to wherever it is imported from | none; we copy the tree and set `cwd` |
| Stream progress | All three repair scripts already print stage markers (`Checking Nebius Sandbox authentication…`, `Baseline:`, `Final verdict:`) | none; we set `PYTHONUNBUFFERED=1` |
| Keep credentials server-side | Scripts read `NEBIUS_*` from the environment at import time | none; the adapter supplies env to the child only |
| Never execute model output on the host | Model code runs only via `contree run` in a disposable VM | none |
| Read results | Reports are written to `ROOT` as JSON | none; we read them from the temp dir |

The only places the adapter touches the backend are **read and execute**: copy files, spawn
`workflow.run_workflow`, read JSON. There is no import of `patch_generator` in the API process
(that module raises at import without credentials), no monkey-patching, and no `sys.path`
manipulation of the repository.

---

## 6. Two design notes before I start

**6.1 Rate-limit persistence requires a state file, which means a volume.**

You asked for limits that survive restarts and deployments. That rules out in-memory counters, so
the limiter uses SQLite at `RC_STATE_DIR`. Consequences:

- Locally: a directory under `/tmp`.
- On Fly.io: a **volume mounted at that path** (1 GB is ample, well under $0.15/month).
- Single-machine assumption is safe because we run **one** API machine. If it is ever scaled to
  two, the limiter and the concurrency lock must move to a shared store — I will document that
  constraint in `api/README.md` rather than leave it implicit.
- Concurrency: the global "one at a time" rule is enforced by an atomic claim **inside the same
  SQLite transaction** as the counters, so 20 simultaneous requests cannot each pass the check.

**6.2 What M1 can and cannot prove**

M1's tests exercise the adapter with a **simulated child process** that emits the same marker
lines and writes the same JSON shapes. That is honest unit/integration coverage of *our* code and
needs no credentials and no spend.

M1 does **not** prove a real Nemotron call or a real `contree` run — by design, that is M2's gated
verification, and it depends on your outstanding requirement: confirming `contree` works from a
clean environment.

---

## 7. Confirmation requested

Before I create the files in §3, please confirm:

1. **File list** — anything to add, remove or rename?
2. **Model name** — the value only (no keys), so M1 can document the expected config and the cost
   table can be pinned to the real model.
3. **State dir** — acceptable to introduce `RC_STATE_DIR` and, later on Fly, one small volume?

On your confirmation I will implement M1 exactly as scoped, run the test suite, and stop for
review.

# RootCause AI — API adapter (Phase 2, M1)

A small FastAPI service that exposes the **existing, unmodified** Python backend to
the React frontend. M1 is the skeleton: routing, job isolation, normalisation,
persistent limits, redaction and tests — with **live runs disabled by default**.

> **M1 does not make any model or sandbox calls.** Every test drives a simulated
> child process. Live execution and the real Nebius verification path are M2 and
> require separate approval.

---

## What this service does

```
POST /api/investigations            → 202 { id }        (live only)
GET  /api/investigations/{id}       → result | status | 404
GET  /api/investigations/{id}/events→ SSE: stage / result / error
GET  /api/investigations/{id}/artifacts/{original.py|candidate.py|report.json}
GET  /api/scenarios                 → 3 scenarios
GET  /api/health                    → mode, limits, queue
```

Each investigation:

1. is rate-limited (durable SQLite counters);
2. gets a **private copy** of the backend's `*.py` modules in `RC_WORKSPACE_ROOT/<job-id>`;
3. runs `api/launcher.py <scenario>` with that directory as cwd, so
   `workflow.ROOT` resolves inside the job and every artifact lands there;
4. streams `RCAI_` marker lines back as stage events;
5. normalises the three inconsistent report shapes into one contract;
6. cleans the workspace up in a `finally`, whatever happens.

The child runs in its own process group and is killed as a group on timeout, so a
wedged grandchild (a hung sandbox CLI) cannot outlive the job.

---

## Design decisions worth knowing

### Live runs are off by default

`LIVE_RUNS_ENABLED=false` makes `POST /api/investigations` return **503** with
`mode: "replay"`. The frontend keeps serving recorded demonstrations — replay is
never blocked by live being unavailable.

### Rate limits are durable

| Limit | Default |
|---|---|
| Per IP per hour | 2 |
| Per IP per day | 5 |
| Global per day | 30 |
| Concurrent | 1 |

Counters live in `RC_STATE_DIR/limits.sqlite3`, so they survive restarts and
redeploys. **Production needs a persistent volume at `RC_STATE_DIR`.**

The check-and-claim runs inside one `BEGIN IMMEDIATE` transaction, so the
concurrency gate and the counters cannot be raced: N simultaneous requests
cannot each observe "under the cap". `tests/test_limits.py` asserts exactly this
with 30 threads against a cap of 5.

**Single-machine assumption.** SQLite serialises writers correctly for one API
machine. If the service is ever scaled horizontally, the limiter and the
concurrency slot must move to a shared store (Redis/Postgres). The interface is
narrow (`check_and_claim`, `release`, `snapshot`) to keep that swap local.

### Verification is never assumed

`api/normalise.py` only emits `verified_fixed` when the backend said so **and**
`final_passed + final_failed` equals the scenario's protected test count with
zero failures. A report that claims success with the wrong counts is downgraded
to `error`. A missing report is `error`, never a pass.

### Stage granularity is honest, and limited

`run_workflow()` captures its own child's stdout, so stages 2–4 are not visible
until it returns. The launcher therefore reports:

- `investigate` running → done — genuinely computed, genuinely streamed;
- `diagnose` running — the backend phase begins;
- `diagnose`, `repair`, `verify` done — all real, emitted on return.

Fine-grained intra-backend progress would need either a backend change (out of
scope by your constraint) or re-implementing the orchestration (which would
diverge from `run_workflow`). M2 can revisit if the backend gains a progress
hook.

### Nothing user-supplied reaches the pipeline

`scenario_id` is a closed enum of three values; extra request fields are rejected
with 422. There is no endpoint that accepts code, paths or prompts. Model output
is only ever executed by `contree` inside a disposable sandbox — never on this
host.

---

## Running locally

```bash
python3 -m venv api/.venv
api/.venv/bin/pip install -r api/requirements-api.txt

# Replay-only (default) — exercises routing without any credentials:
api/.venv/bin/uvicorn api.main:app --port 8000 --reload

# Live (M2+, needs Nebius credentials):
LIVE_RUNS_ENABLED=true api/.venv/bin/uvicorn api.main:app --port 8000
```

Frontend against it:

```bash
cd web && VITE_API_MODE=live API_PROXY_TARGET=http://127.0.0.1:8000 npm run dev
```

---

## Tests

```bash
api/.venv/bin/python -m pytest -q
```

| File | Covers |
|---|---|
| `test_contract.py` | field-level parity with `web/src/lib/contract.ts`; enum closed; test counts match the repo |
| `test_normalise.py` | all three report shapes, `refund_sign_error`, missing `elapsed_seconds`, count-mismatch downgrade |
| `test_redact.py` | secrets removed from logs, tracebacks, headers and key/value forms |
| `test_limits.py` | per-IP hour/day, global day, restart persistence, stale reclaim, 30-thread race |
| `test_workspace.py` | isolation, only top-level `.py`, no `.env`, traversal blocked, cleanup |
| `test_routes.py` | health, scenarios, 503 when disabled, 422 on bad input, 429s, artifact whitelist, no secret in any response |
| `test_launcher.py` | the **real** launcher against the **real** backend: stage 1 genuinely runs for all three scenarios with no credentials; missing key is reported, not crashed; nothing is written into the repo |

---

## Not in M1

- Live Nemotron calls and real `contree` sandbox runs (M2, gated)
- Proving `contree` works from a clean environment — outstanding verification
- Light/dark theming and live/replay badges in the UI (M3)
- Container image, Fly.io/Cloudflare provisioning (M5, needs approval)
- `sandbox_ready` is reported as `null` — not claimed until M2 measures it

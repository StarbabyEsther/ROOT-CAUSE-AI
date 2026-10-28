# Demo day checklist

Print this. Tick in order. **Stop at any unticked line.**

## Before you touch anything

- [ ] `git log --oneline -1` shows the Arena branch tip, not `main`
- [ ] `api/.venv/bin/python -m api.preflight` → `READY` (0 blockers)
- [ ] You can name the value of `NEBIUS_MODEL` (it drives cost and quality)

## Prove the pipeline works, locally

- [ ] `api/.venv/bin/python -m api.preflight --live` → one real run, verdict
      `verified_fixed`, 6/6 tests. **This is the only proof that `contree` works
      outside your laptop's existing auth.** If it fails here, it will fail in
      production — fix it before deploying.

## Ship

- [ ] `fly deploy` → `curl .../api/health` returns `ok:true`
- [ ] Cloudflare Pages builds `web/` with `VITE_API_MODE=live`
- [ ] Site loads; header pill reads **Replay demo** (correct — live still off)
- [ ] `fly secrets set LIVE_RUNS_ENABLED=true`
- [ ] Site loads; header pill reads **Live AI**
- [ ] Run one investigation from the deployed site → badge says **Live investigation**,
      verdict `verified_fixed`, 6/6 pass
- [ ] Run three more times → fourth request shows the **recorded demonstration**
      banner with the hourly-limit reason. That is the limiter working, and it is
      safe to demo: the site never breaks, it degrades.

## What to say if a judge asks

| Question | Answer |
|---|---|
| Is this really calling the model? | Yes — the badge on the result says **Live investigation**, and `mode: "live"` comes from the run itself. |
| What happens when the quota runs out? | It falls back to a recorded run and labels it **Recorded demonstration**. |
| Where are the API keys? | Server-side only, in Fly secrets. The browser bundle contains none. |
| Can someone inject code? | No endpoint accepts code. `scenario_id` is a three-value enum. |
| Could the AI patch reach production? | It never touches the repo; it runs only in a disposable sandbox against protected tests. |

## Kill switch

```bash
fly secrets set LIVE_RUNS_ENABLED=false
```

Reverts the site to labelled replay in seconds. Use it if anything looks wrong on
stage — the demo keeps working.

# Deploying RootCause AI (hackathon day)

Two components, deliberately separate:

| Part | Where | Notes |
|---|---|---|
| React site | Cloudflare Pages (free) | static build of `web/` |
| FastAPI adapter | Fly.io (`shared-cpu-1x`, 512 MB) | holds the credentials |
| Streamlit app | Streamlit Cloud | **unchanged**, keeps its existing URL |

**Nothing here has been deployed. Run the steps in order, and stop at any FAIL.**

---

## 0. Gate: preflight must pass

```bash
api/.venv/bin/python -m api.preflight          # config, imports, contree auth, tests
api/.venv/bin/python -m api.preflight --live   # + one real investigation (~$0.0006)
```

The `--live` run is the only way to know that `contree` works from a clean
environment — that item has been outstanding since the Phase 2 plan. Do not
deploy live runs before it passes.

---

## 1. Deploy the API to Fly.io

```bash
fly launch --no-deploy --name rootcause-ai-api --region iad --copy-config
fly volumes create rcai_state --size 1 --region iad        # 1 GB, ~$0.15/mo
fly secrets set \
  NEBIUS_API_KEY=... \
  NEBIUS_MODEL=... \
  CONTREE_PROJECT_ID=... \
  CONTREE_TOKEN=...                                        # if your contree auth needs it
fly deploy
```

Verify:

```bash
curl https://rootcause-ai-api.fly.dev/api/health
# {"ok":true,"liveEnabled":false,"mode":"replay",...,"sandboxReady":null}
```

`liveEnabled` is `false` — that is correct until step 3.

**Keep `LIVE_RUNS_ENABLED=false` for now.** The site works in replay mode, which
is a legitimate, fully-labelled product state.

---

## 2. Deploy the site to Cloudflare Pages

Cloudflare dashboard → Workers & Pages → Create → Pages → Connect to Git:

| Setting | Value |
|---|---|
| Repository | `StarbabyEsther/ROOT-CAUSE-AI` |
| Branch | `arena/0eaa482c-root-cause-ai` (or a dedicated `deploy` branch after merge) |
| Framework preset | Vite |
| Root directory | `web` |
| Build command | `npm ci && npm run build` |
| Output directory | `dist` |
| Env var | `VITE_API_MODE=live` |

`web/public/_redirects` already provides the SPA fallback, so deep links such as
`/lab/monetary_precision` resolve.

Then point the API at the Pages origin and finish the wiring:

```bash
fly secrets set RC_ALLOWED_ORIGINS="https://<your-site>.pages.dev"
```

The browser calls the API through a Pages proxy. Add a `functions/api/[[path]].ts`
worker that forwards `/api/*` to `https://rootcause-ai-api.fly.dev`, or (simpler)
set `VITE_API_BASE=https://rootcause-ai-api.fly.dev` and allow that origin in CORS.
The adapter already sends `Access-Control-Allow-Origin` for allowlisted origins only.

---

## 3. Turn live runs on

Only after step 0 passed with `--live`:

```bash
fly secrets set LIVE_RUNS_ENABLED=true
```

Watch it for the first hour:

```bash
fly logs
curl https://rootcause-ai-api.fly.dev/api/health     # queue + remaining
```

Kill switch, any time, no redeploy:

```bash
fly secrets set LIVE_RUNS_ENABLED=false
```

The site immediately falls back to recorded investigations, labelled as such.

---

## Costs

| Item | Monthly |
|---|---|
| Cloudflare Pages | $0 |
| Fly machine (`shared-cpu-1x`, 512 MB, scale to zero) | ~$0–3 |
| Fly volume, 1 GB | ~$0.15 |
| Nemotron inference at 30 runs/day | ~$0.5–1.5 |

No paid resource is created by any file in this repository. The volume and the
machine are the only chargeable items, and both are created by you in step 1.

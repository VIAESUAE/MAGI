# MAGI — Architecture and implementation

This document describes the stack, lifecycle, and main files. For a minimal run guide, use [../QUICKSTART.md](../QUICKSTART.md).

## Stack

| Layer | Role |
|--------|--------|
| **API** | LiteLLM for unified model calls, retries, timeouts |
| **Backend** | Python + FastAPI, async `asyncio` where needed, **SSE** for `/magi/resolve/stream` |
| **Frontend** | Vue 3, state machine in `App.vue` (no vue-router for the main flow) |

## Lifecycle (state machine)

```
STANDBY → ARCHITECT_ANALYSIS → TRI_CORE_PROCESSING → RESOLUTION
            ↑                        │
            └──────────────────────────┘
```

Switches are centralized in `App.vue`.

## High-level flow

1. **Architect** — Aligns the user’s natural-language request; may ask for clarification; can emit a **Resolution draft** (JSON) when ready.
2. **Tri core** — Three blind nodes (Melchior, Balthasar, Casper) run against the draft in parallel, isolated context.
3. **Synthesis** — Bus summary and second round, then a final **clerk**-style resolution (see `magi_core.py` and SSE events).

## SSE

The browser consumes **Server-Sent Events** from `POST /magi/resolve/stream` with JSON `data:` lines. Implementation: `frontend/src/api/magiStream.js`; orchestration: `App.vue`.

## Relevant files

- `backend/app/main.py` — FastAPI app, CORS
- `backend/app/api_router.py` — Routes for preflight, stream, OpenRouter list
- `backend/app/magi_core.py` — Core orchestration, node calls, I18N strings, prompts
- `backend/app/architect.py` — Resolution draft heuristics / clarification
- `backend/app/synthesizer.py` — Verdict / consensus copy per locale
- `frontend/src/api/magiApi.js` — Non-stream API calls
- `frontend/src/api/magiStream.js` — Stream consumer
- `frontend/src/views/*` — Standby, architect, tri-core, resolution

## Vite dev proxy

`vite.config.js` maps `/api/*` to `http://localhost:8000` so the app can call `fetch('/api/...')` in development.

## External services

- **OpenRouter** — Model catalog and gateway; key stays in the user’s browser and is passed to the backend for requests. Free models may return `No endpoints found` or rate limits; that is an upstream or quota issue, not a frontend routing bug.

## Preflight and diagnostics

Preflight checks each node with the chosen model before the full run. The resolution view exposes **Node diagnostics** for errors and summaries.

## Local storage

Config (keys, model ids, flags) is stored in `localStorage` in the browser. The backend is not a multi-user key vault; protect your machine and browser profile.

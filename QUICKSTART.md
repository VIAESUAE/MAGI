# MAGI — Quick start

## Overview

MAGI is a multi-agent consensus stack: Vue 3 (EVA-style UI), FastAPI + LiteLLM, **SSE** streaming, and **OpenRouter** for model choice.

## Prerequisites

- Node.js 18+ (`node -v`, `npm -v`)
- Python 3.10+ (`python3 -V`)
- Optional: place `FOT-MatissePro.ttf` in `frontend/public/fonts/` for the intended typeface

## Install dependencies (once)

```bash
cd /path/to/MAGI/backend
pip install -r requirements.txt

cd /path/to/MAGI/frontend
npm install
```

## Run (two terminals)

**Terminal A — backend (must run from project root `MAGI`)**

```bash
cd /path/to/MAGI
python3 -m uvicorn backend.app.main:app --reload --port 8000
```

**Terminal B — frontend**

```bash
cd /path/to/MAGI/frontend
npm run dev
```

Open `http://localhost:5173` (or the URL Vite prints).

## Flow on the app

1. **STANDBY** — enter OpenRouter API key; optional **Fetch OpenRouter Models**; **Save config**; **Start analysis** (runs preflight first).
2. **ARCHITECT_ANALYSIS** — follow the architect; add detail as prompted.
3. **TRI_CORE_PROCESSING** — wait for the three nodes and SSE; then open the report when ready.
4. **RESOLUTION** — read the verdict and **Node diagnostics** for per-node errors.

**Frontend debug mode** does not call the real backend; it is for UI-only testing.

## macOS helper scripts

- `start-dev.command` — start backend and frontend
- `start-dev-frontend-only.command` — frontend only, if present

## Troubleshooting

| Symptom | What to check |
|--------|-----------------|
| `uvicorn: command not found` | Use `python3 -m uvicorn ...` and ensure dependencies are installed |
| `No module named 'app'` | Run from **MAGI root** with `backend.app.main:app`, not `app.main` from inside `backend/` only |
| Nodes ERROR / 429 / 404 | Model id, free-tier limits, or rate limits; change model or key; see resolution diagnostics |

## Security

The API key is kept in the browser **localStorage** and sent to **your** backend only. Do not commit keys to git or share screenshots of keys.

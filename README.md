# MAGI (Multi-Agent Consensus System)

An EVA-inspired multi-agent consensus UI: three models in parallel blind review, SSE streaming, two review rounds, and synthesis.

## Start here

- **Quick start:** [QUICKSTART.md](./QUICKSTART.md)
- **Architecture and implementation notes:** [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- **Privacy (hosted backend vs self-host):** [PRIVACY.md](./PRIVACY.md) · [SECURITY.md](./SECURITY.md)

## Install (once per machine)

- Backend: `cd backend && pip install -r requirements.txt`
- Frontend: `cd frontend && npm install`

## Run locally

**Backend** (from the **MAGI project root**, not from inside `backend/` only):

```bash
cd /path/to/MAGI
python3 -m uvicorn backend.app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd /path/to/MAGI/frontend
npm run dev
```

Open the URL printed in the terminal (usually `http://localhost:5173`), set your OpenRouter key and models, then start the flow.

On macOS you can try `start-dev.command` in the project root to launch both (requires Python 3 and Node).

## Layout

- `backend/` — FastAPI, `/magi/resolve`, `/magi/resolve/stream` (SSE), preflight, OpenRouter model list
- `frontend/` — Vue 3, four main views, SSE client, Vite dev proxy from `/api` to `http://localhost:8000`
- `LICENSE` — see file for terms

## UI languages

The interface supports **Traditional Chinese** (`zh`), **English** (`en`), and **Japanese** (`ja`), selectable in the app. The default follows the browser language on first visit when no preference is stored.

## Deploy backend on Render

`requirements.txt` lives under **`backend/`**, not the repo root. In the Render dashboard: **Settings → Root Directory** = `backend`. **Build:** `pip install -r requirements.txt`. **Start:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

Alternatively, connect a [Blueprint](https://render.com/docs/infrastructure-as-code) using [`render.yaml`](./render.yaml) at the repository root.

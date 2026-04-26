# MAGI backend

FastAPI service: forwards calls to three models via LiteLLM, runs arbitration and **SSE** streaming for `/magi/resolve/stream`.

## Run (recommended: from monorepo root)

From the **MAGI** repository root:

```bash
pip install -r backend/requirements.txt
python3 -m uvicorn backend.app.main:app --reload --port 8000
```

## Run (only if `backend` is the working directory)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Use whichever matches how your shell resolves the `app` package; the **first** form avoids `ModuleNotFoundError` when the repo is laid out as this project expects.

## Requirements

See `requirements.txt` (FastAPI, Uvicorn, LiteLLM, etc.).

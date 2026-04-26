import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api_router import router


def _cors_origins() -> list[str]:
    """
    Browsers reject Access-Control-Allow-Origin: * together with
    Access-Control-Allow-Credentials: true. We do not use credentialed
    fetches, so allow_credentials is False; keeping * is fine.

    Set MAGI_CORS_ORIGINS to a comma-separated list to restrict origins, e.g.
    https://you.github.io,http://localhost:5173
    """
    raw = (os.getenv("MAGI_CORS_ORIGINS") or "").strip()
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    return ["*"]


app = FastAPI()

@app.get("/")
async def root():
    """So visiting the service URL in a browser does not 404; API routes live under /magi, /docs, /healthz."""
    return {
        "service": "MAGI API",
        "docs": "/docs",
        "health": "/healthz",
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    # Must be False when allow_origins is ["*"] — otherwise browsers block cross-site fetch with "Failed to fetch".
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

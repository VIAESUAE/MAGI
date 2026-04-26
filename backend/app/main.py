import logging
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api_router import router

# Avoid litellm printing request/response details to process logs.
try:
    import litellm

    if hasattr(litellm, "set_verbose"):
        litellm.set_verbose = False
    if hasattr(litellm, "suppress_debug_info"):
        litellm.suppress_debug_info = True
except Exception:
    pass

_log = logging.getLogger("magi")


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


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    """Do not return raw exception text (may contain upstream or redacted key material) to clients."""
    if isinstance(exc, HTTPException):
        return await http_exception_handler(request, exc)
    if isinstance(exc, RequestValidationError):
        return await request_validation_exception_handler(request, exc)
    if (os.getenv("MAGI_DEBUG") or "").strip() in ("1", "true", "yes"):
        _log.exception("unhandled")
    else:
        _log.error("unhandled: %s (set MAGI_DEBUG=1 for trace)", type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={"detail": "Service error. If this persists, try again or use a self-hosted backend."},
    )

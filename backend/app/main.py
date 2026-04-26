from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api_router import router

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

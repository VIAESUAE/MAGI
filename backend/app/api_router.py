from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from .magi_core import iter_magi_resolve_sse, list_openrouter_models, preflight_models, process_magi

router = APIRouter()


@router.get('/healthz')
async def healthcheck():
    return {'status': 'ok'}


@router.post('/magi/resolve')
async def magi_resolve(request: Request):
    data = await request.json()
    return await process_magi(data)


@router.post('/magi/preflight')
async def magi_preflight(request: Request):
    data = await request.json()
    return await preflight_models(data)


@router.post('/magi/openrouter/models')
async def magi_openrouter_models(request: Request):
    data = await request.json()
    return await list_openrouter_models(data)


@router.post('/magi/resolve/stream')
async def magi_resolve_stream(request: Request):
    data = await request.json()

    async def event_stream():
        async for chunk in iter_magi_resolve_sse(data):
            yield chunk

    return StreamingResponse(
        event_stream(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        },
    )

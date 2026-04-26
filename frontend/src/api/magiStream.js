/**
 * POST SSE: consumes FastAPI StreamingResponse (text/event-stream) with JSON data lines.
 */
import { getApiUrl } from './apiBase.js'

/** Render cold start / TLS can exceed 15s; tunable via VITE_SSE_CONNECT_MS in build. */
const connectTimeoutMs =
  Number(import.meta.env.VITE_SSE_CONNECT_MS) > 0
    ? Number(import.meta.env.VITE_SSE_CONNECT_MS)
    : 60000

/**
 * No SSE chunks are sent while the server runs tri-core LLM calls; gaps of minutes are possible
 * on free models. Default 45s was far too short. Override with VITE_SSE_IDLE_MS (build-time).
 */
const streamIdleTimeoutMs =
  Number(import.meta.env.VITE_SSE_IDLE_MS) > 0
    ? Number(import.meta.env.VITE_SSE_IDLE_MS)
    : 600000

export async function consumeMagiStream(body, { onEvent, signal } = {}) {
  const connectController = new AbortController()
  const connectTimeoutId = setTimeout(() => {
    connectController.abort(
      new Error(`SSE connection timeout after ${connectTimeoutMs / 1000}s (try VITE_SSE_CONNECT_MS / check Render sleep).`)
    )
  }, connectTimeoutMs)

  if (signal) {
    signal.addEventListener(
      'abort',
      () => {
        connectController.abort(signal.reason || new DOMException('Aborted', 'AbortError'))
      },
      { once: true }
    )
  }

  let res
  try {
    res = await fetch(getApiUrl('/api/magi/resolve/stream'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
      body: JSON.stringify(body),
      signal: connectController.signal
    })
  } catch (err) {
    clearTimeout(connectTimeoutId)
    if (connectController.signal.aborted && !(signal && signal.aborted)) {
      throw new Error(
        `Unable to connect to stream endpoint within ${connectTimeoutMs / 1000}s (Render may be waking from sleep).`
      )
    }
    throw err
  } finally {
    clearTimeout(connectTimeoutId)
  }

  if (!res.ok) {
    const text = await res.text()
    let detail = text
    try {
      const j = JSON.parse(text)
      detail = j.detail ?? text
    } catch {
      /* keep text */
    }
    throw new Error(detail || `HTTP ${res.status}`)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let streamEnded = false
  const timeoutMs = streamIdleTimeoutMs
  let timeoutId = null
  let timedOut = false

  const clearWatchdog = () => {
    if (timeoutId) {
      clearTimeout(timeoutId)
      timeoutId = null
    }
  }

  const kickWatchdog = () => {
    clearWatchdog()
    timeoutId = setTimeout(async () => {
      timedOut = true
      try {
        await reader.cancel()
      } catch {
        /* ignore */
      }
    }, timeoutMs)
  }

  const flushBlocks = (text) => {
    let rest = text
    let idx = -1
    const findBoundary = (source) => {
      const lf = source.indexOf('\n\n')
      const crlf = source.indexOf('\r\n\r\n')
      if (lf === -1) return crlf
      if (crlf === -1) return lf
      return Math.min(lf, crlf)
    }
    while ((idx = findBoundary(rest)) !== -1) {
      const rawBlock = rest.slice(0, idx)
      const step = rest.startsWith('\r\n\r\n', idx) ? 4 : 2
      rest = rest.slice(idx + step)

      const lines = rawBlock.replace(/\r\n/g, '\n').split('\n')
      for (const line of lines) {
        if (!line.startsWith('data:')) continue
        const jsonText = line.slice(5).trim()
        if (!jsonText) continue
        const evt = JSON.parse(jsonText)
        onEvent?.(evt)
        kickWatchdog()
        if (evt?.event === 'done') streamEnded = true
      }
    }
    return rest
  }

  kickWatchdog()
  while (true) {
    const { done, value } = await reader.read()
    if (value) {
      buffer += decoder.decode(value, { stream: true })
    }
    buffer = flushBlocks(buffer)
    if (streamEnded) {
      await reader.cancel()
      break
    }
    if (done) {
      if (buffer.trim()) {
        const lines = buffer.replace(/\r\n/g, '\n').split('\n')
        for (const line of lines) {
          if (!line.startsWith('data:')) continue
          const jsonText = line.slice(5).trim()
          if (!jsonText) continue
          const evt = JSON.parse(jsonText)
          onEvent?.(evt)
          kickWatchdog()
          if (evt?.event === 'done') streamEnded = true
        }
      }
      clearWatchdog()
      if (!streamEnded) {
        if (timedOut) {
          throw new Error(
            `SSE stream idle timeout after ${timeoutMs / 1000}s (raise VITE_SSE_IDLE_MS on build, or reduce model latency).`
          )
        }
        throw new Error('SSE stream ended unexpectedly before done signal.')
      }
      break
    }
  }
  clearWatchdog()
}

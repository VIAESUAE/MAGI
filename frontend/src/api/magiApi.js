export async function preflightMagi(tokens, models = {}, locale = 'zh') {
  const res = await fetch('/api/magi/preflight', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tokens, models, locale })
  })

  const text = await res.text()
  let data = null
  try {
    data = JSON.parse(text)
  } catch {
    data = { detail: text }
  }

  if (!res.ok) {
    throw new Error(data?.detail || `HTTP ${res.status}`)
  }
  return data
}

export async function fetchOpenRouterModels(token) {
  const res = await fetch('/api/magi/openrouter/models', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token })
  })

  const text = await res.text()
  let data = null
  try {
    data = JSON.parse(text)
  } catch {
    data = { detail: text }
  }

  if (!res.ok) {
    throw new Error(data?.detail || `HTTP ${res.status}`)
  }
  return data?.models || []
}

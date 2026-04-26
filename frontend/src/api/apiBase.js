/**
 * Development: requests use /api/... and Vite proxies to the local backend (see vite.config.js).
 * Production (e.g. GitHub Pages): VITE_API_BASE is baked in at **build** time (GitHub Actions secret
 * `VITE_API_BASE`), e.g. https://magi-xxxx.onrender.com — no `/api` suffix, no trailing slash.
 * If it is empty, the browser calls same-site `/api/...` on github.io, which is wrong and
 * causes timeouts / 404s for preflight, SSE, etc.
 */
function resolvedApiBase() {
  const base = import.meta.env.VITE_API_BASE
  if (base == null) return ''
  return String(base).trim()
}

/** True when a backend origin is embedded in the production bundle. */
export function isApiBaseConfigured() {
  return resolvedApiBase() !== ''
}

/**
 * If this is a likely misconfigured production Pages build, return a short user-facing message.
 * Otherwise null.
 */
export function getProdApiConfigWarning() {
  if (!import.meta.env.PROD) return null
  if (isApiBaseConfigured()) return null
  if (typeof window === 'undefined') return null
  const h = window.location?.hostname || ''
  if (!h.includes('github.io')) return null
  return (
    '本頁構建時未設置 VITE_API_BASE，API 仍指向 github.io 而非 Render，會導致預檢/串流超時。' +
    '請在倉庫 Settings → Secrets and variables → Actions 新增密鑰，名稱 VITE_API_BASE，' +
    ' 值為你的後端根網址（如 https://xxx.onrender.com，勿加 /api 與末尾斜槓），' +
    '然後手動執行 “Deploy frontend to GitHub Pages” 或再 push 觸發重新構建。'
  )
}

export function getApiUrl(path) {
  const origin = resolvedApiBase()
  if (origin !== '') {
    const withoutTrailing = origin.replace(/\/$/, '')
    const withoutApi = path.replace(/^\/api/, '')
    return `${withoutTrailing}${withoutApi.startsWith('/') ? withoutApi : `/${withoutApi}`}`
  }
  return path
}

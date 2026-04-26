/**
 * Development: requests use /api/... and Vite proxies to the local backend (see vite.config.js).
 * Production (e.g. GitHub Pages): set VITE_API_BASE to your Render service origin, e.g.
 *   https://magi-xxxx.onrender.com
 *   (no trailing slash). Build: VITE_API_BASE=https://... npm run build
 */
export function getApiUrl(path) {
  const base = import.meta.env.VITE_API_BASE
  if (base != null && String(base).trim() !== '') {
    const origin = String(base).replace(/\/$/, '')
    const withoutApi = path.replace(/^\/api/, '')
    return `${origin}${withoutApi.startsWith('/') ? withoutApi : `/${withoutApi}`}`
  }
  return path
}

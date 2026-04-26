/**
 * Maps browser languages to I18N keys: zh, en, ja.
 * Falls back to en when no match.
 */
export function detectBrowserLocale() {
  if (typeof navigator === 'undefined') return 'en'
  const list = []
  if (navigator.language) list.push(navigator.language)
  if (Array.isArray(navigator.languages)) list.push(...navigator.languages)
  for (const raw of list) {
    if (!raw || typeof raw !== 'string') continue
    const full = raw.toLowerCase()
    const base = full.split('-')[0]
    if (base === 'ja') return 'ja'
    if (base === 'en') return 'en'
    if (base === 'zh') return 'zh'
  }
  return 'en'
}

export function getInitialLocale() {
  try {
    if (typeof localStorage === 'undefined') return detectBrowserLocale()
    const saved = localStorage.getItem('magi_locale')
    if (saved === 'zh' || saved === 'en' || saved === 'ja') return saved
  } catch {
    /* ignore */
  }
  return detectBrowserLocale()
}

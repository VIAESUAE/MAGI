import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Subpath for GitHub project pages, e.g. VITE_BASE_PATH=/MAGI/ for https://user.github.io/MAGI/
const viteBase = () => {
  const p = process.env.VITE_BASE_PATH
  if (!p || p === '/') return '/'
  return p.endsWith('/') ? p : `${p}/`
}

export default defineConfig({
  base: viteBase(),
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})

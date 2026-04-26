# MAGI frontend

Vue 3 + Vite. Four main views, one state machine in `App.vue`, two API clients (`magiApi.js`, `magiStream.js`).

## Tree

```
frontend/
├── index.html
├── package.json
├── vite.config.js          dev: proxy /api -> http://localhost:8000
├── public/fonts/           FOT-MatissePro (optional)
└── src/
    ├── main.js
    ├── style.css
    ├── App.vue             state + i18n + SSE
    ├── utils/localeDetect.js
    ├── i18n/magiDocs.js
    ├── api/
    │   ├── magiApi.js
    │   └── magiStream.js
    └── views/
        ├── StandbyView.vue
        ├── ArchitectAnalysisView.vue
        ├── TriCoreProcessingView.vue
        ├── ResolutionView.vue
        └── WelcomeView.vue
```

## State machine

No vue-router for the main flow: transitions live in `App.vue`.

## Commands

```bash
npm install
npm run dev      # Vite, default :5173
npm run build    # output: dist/
```

The backend should run on port **8000** in dev; Vite proxies `/api` to it. Change the target in `vite.config.js` if needed.

## Production API (GitHub Pages, etc.)

Vite dev uses `/api` → proxy → local backend. For a static build, set **`VITE_API_BASE`** to your **Render service origin** (the same host you use for `/docs`):

```bash
VITE_API_BASE=https://your-name.onrender.com npm run build
```

Upload the `dist/` output to GitHub Pages. The app will call `https://your-name.onrender.com/magi/...` (the `/api` prefix is stripped to match the FastAPI routes).

### Automated deploy (optional)

The repo includes [`.github/workflows/deploy-frontend-pages.yml`](../.github/workflows/deploy-frontend-pages.yml). After you:

1. Set **Repository secret** `VITE_API_BASE` to your Render URL (e.g. `https://magi-xxx.onrender.com`).
2. If the site is **project pages** (`https://user.github.io/REPO/`), set **Repository variable** `VITE_BASE_PATH` to `/REPO/` (with slashes).
3. In GitHub: **Settings → Pages → Source: GitHub Actions**.

Pushing to `main` will build and publish the frontend. You do not need to click “set up workflow” in the Actions tab if this file is already in the repo.

## Notes

- **Keys and settings** use browser `localStorage`. See [`.env.example`](./.env.example) for `VITE_API_BASE` only; never put API keys in env files that ship to the client.
- The language switcher supports Traditional Chinese, English, and Japanese (see `App.vue` I18N).

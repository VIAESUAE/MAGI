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

## Notes

- API base path in dev is the Vite proxy `/api` (not a separate `VITE_` base unless you add one for production).
- Keys and settings use browser `localStorage`.
- The language switcher supports Traditional Chinese, English, and Japanese (see `App.vue` I18N).

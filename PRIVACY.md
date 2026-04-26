# Privacy & data handling (MAGI)

This document describes the **intended** behaviour of the open-source project. A **particular** deployment (Render, your own server, a fork) may add logging or analytics—verify that host’s own policy.

## What this software does

- **In the browser:** API keys and model selections are stored in `localStorage` (unless you change the code). The author of a *public static site* cannot read your hard drive.
- **When you run a flow:** The browser sends your key (over **HTTPS** in the shipped setup) to the **MAGI backend base URL** you configure (`VITE_API_BASE` for static builds, or the Vite dev proxy in development). The backend then calls model providers (e.g. via LiteLLM → OpenRouter) using that key **for that request** in process memory. The codebase is not designed to **store** API keys in a database.

## What this does *not* guarantee

- It is **not** a promise that the **operator of the hosted backend** (or an attacker of that host) is cryptographically unable to see keys or request bodies. In the usual threat model, they are on the path.
- **OpenRouter and upstream model providers** have their own terms, logging, and billing; you must read their policies.
- **Client-side** risk (malicious extensions, compromised browser, XSS in any dependency) is outside the scope of a single repo policy.

## Recommendations

- For **public demo / shared** instances, prefer **free or low-risk** API keys. For high-value **paid** master keys, **self-host** the backend from this repository so you control the host and can audit the running image.
- Review the in-app **“Privacy & data”** text (it may be more up-to-date for a given release than this file).

## Changes & contact

- Source: see commit history. For security vulnerabilities, see [SECURITY.md](./SECURITY.md).

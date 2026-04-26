# Security

## Reporting a vulnerability

- Open a **private** security advisory on GitHub (if the repository is on GitHub), or email the maintainer if you have a private channel.
- Please include: affected component, steps to reproduce, and impact. Do not post working exploits publicly until a fix is released.

## Project goals (not guarantees)

- Minimize what is returned in API error messages (keys and bearer tokens are redacted where practical).
- Avoid `allow_credentials` + `*` CORS misconfiguration; keep dependencies updated.
- Do not intentionally log full request bodies containing API keys in application code. **Platform** logs (Render, reverse proxy) may still exist—configure them with least privilege for your deployment.

## Out of scope

- **OpenRouter / model vendor** security and data handling.
- **User device** and browser extension compromise.

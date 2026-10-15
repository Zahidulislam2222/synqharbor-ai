# Self-hosting

The current website produces static HTML, CSS, JavaScript, fonts and media. It
requires no application database, account service or inference provider.

## Build

Use Node.js 24 LTS and npm. Install the exact lockfile dependencies:

```bash
npm ci
```

Copy `.env.example` to `.env.local` and configure `NEXT_PUBLIC_SITE_URL` with the
intended HTTPS origin. This value is public and embedded during build. Never
place a secret in a `NEXT_PUBLIC_` variable.

```bash
npm test
npm run typecheck
npm run lint
npm run build
```

Serve `out/` with a static server. Keep directory index handling, a true 404 response
using `404.html`, correct MIME types, HTTPS and media range requests. A static
export does not supply request-dependent API routes or server actions.

## Public configuration and content

- `src/config/ui.ts`: public origin parsing, routes, media, motion and status limits.
- `src/content/`: product copy, navigation, page content and workspace initial state.
- `next.config.ts`: export/build settings.
- `.env.example`: supported public environment-variable names.

Self-hosted fonts avoid runtime font-CDN requests. The hero image and silent motion
loop are shipped with the site. No model-provider key is needed to run the website.

## Release and rollback

Build locally from reviewed source. Compare the current deployment with its local
release manifest before replacing it. Upload a new versioned directory, validate
its server configuration, check health, then atomically switch the active release.
Keep the previous version and an off-host archive. Prove file parity after activation.

On a shared host, use a distinct application identity, loopback-only HTTP publishing,
bounded resources and project-specific reverse-proxy configuration. Do not alter
unrelated host services or expose a Docker socket. Generated JavaScript must work
under the actual Content Security Policy, not only a local development server.

## Operator responsibilities

The operator owns DNS, certificates, patching, log handling, access recovery and
monitoring. The maintainer’s infrastructure is not included in the software license.
The future authenticated platform requires separate provisioning, schema migrations,
data backups and an explicit processing schedule before real customer data is accepted.

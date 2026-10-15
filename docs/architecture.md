# Architecture

Next.js exports static routes. React and Motion handle browser interactions. A hardened static server sits behind Caddy HTTPS and Cloudflare delivery. Browser workspace state does not leave the tab.

## Current website

Next.js exports static routes. React and Motion handle browser interactions. A hardened static server sits behind Caddy HTTPS and Cloudflare delivery. Browser workspace state does not leave the tab.

## Future control plane

FastAPI and PostgreSQL own identities, membership, tasks, runs, artifacts, approvals, grants and an append-only application audit trail. A modular monolith keeps one authoritative task dispatcher.

## Execution boundary

Outbound runners accept bounded assignments. Coding work runs in disposable isolated environments; the web server never executes arbitrary agent-generated commands. Tools enforce authorization independently of model output.

See [the documentation index](README.md) and [the full build plan](../BUILD-PLAN.md).

# Self-hosting frontend and backend

## Prerequisites

Use Node.js 24 LTS, Python 3.12, PostgreSQL, an installed local Ollama service and a checksum-verified rootless gVisor runtime on a supported Linux host. Static website hosting alone does not run the authenticated API or worker. Review [deployment concepts](https://fastapi.tiangolo.com/deployment/concepts/) and the [gVisor production guide](https://gvisor.dev/docs/user_guide/production/).

## Build and configure

```sh
npm ci
npm test
npm run typecheck
npm run lint
npm run build
python3 -m venv .venv-api
.venv-api/bin/python -m pip install -r backend/requirements.txt
```

Copy safe settings from `.env.example` into a private `backend/.env`. Generate a fresh session secret. For HTTPS set the exact `SH_PUBLIC_ORIGIN`, secure cookies, host-prefixed cookie name and allowed host. Set `SH_REGISTRATION_ENABLED=false` for operator-managed enrollment. Set the runtime PostgreSQL URL and a separate migration URL only in the migration environment. Revoke runtime table/schema ownership, schema CREATE, superuser and BYPASSRLS; grant required DML and migration-version reads.

Configure loopback inference, complete installed model digests, Builder/coding/Reviewer bindings and resource/time/concurrency limits. Configure the verified runner binary, minimal read-only Python rootfs and private job directory. Expected test answers remain outside the guest. Repository targets point only at dedicated operator-authorized working trees.

```sh
cd backend
../.venv-api/bin/python -m app.database
../.venv-api/bin/python -m app.manage create-user --email USER_EMAIL --name USER_NAME
../.venv-api/bin/uvicorn app.main:create_app --factory --host 127.0.0.1 --port API_PORT --no-proxy-headers --no-access-log
# Separate supervised service, same runtime configuration:
../.venv-api/bin/python -m app.worker
```

## Serve and supervise

Serve `out/` with nginx and route `/api/` from the same HTTPS origin to the loopback API. Caddy or an equivalent maintained proxy terminates TLS. Use exact release-generated CSP hashes, correct MIME/media range/404 handling and immutable caching only for public hashed assets. Never cache private API content.

Use least-privilege systemd users, protected secret files, bounded services, automatic restart, persistent database storage and encrypted off-host backups. On Ubuntu, a narrow executable AppArmor user-namespace profile may be required for rootless runsc; do not disable host-wide protections. Verify the sandbox under the actual service identity and systemd restrictions.

SQLite is a tested local-development option. It is not the hosted database topology. No cloud API key or paid inference fallback is required. Review [core workflows](core-engine.md), [operations](operations.md), [configuration](configuration.md) and [release checklist](release-checklist.md).

Maintained by [Zahidul Islam](https://github.com/Zahidulislam2222). See the [documentation index](README.md) and [delivery roadmap](roadmap.md).

## Separate API and repository writer identities

When API and worker users differ, the API needs read-only traversal and Git/source metadata access to each operator-granted repository. Keep job directories private and repository writes worker-only. Apply an API-specific exact `safe.directory` trust configuration, disable optional Git locks for snapshot reads, and maintain inherited read ACLs on repository metadata. Publication preserves the existing index access policy. Verify snapshot submission and a subsequent read after publication under the actual API identity; a mocked repository test does not establish these operating-system permissions.

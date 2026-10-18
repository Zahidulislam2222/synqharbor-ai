# Operations and release runbook

## Prepare and deploy

Confirm the target host and available capacity using native inventories. Capture the current live files/configuration, compare with the prior local manifest, and reconcile drift before editing. Build from pinned dependencies with the intended public origin. Run tests, types, lint, dependency/security scans and a fresh-context source review. Render deployment settings centrally; secrets remain in private environment files with restricted permissions.

Create a new versioned release and manifest. Provision only the project-specific service account, database identities/storage, local inference and protected runner within approved existing capacity. Migrate using the dedicated migration role; web/worker environments receive only runtime credentials. Validate reverse-proxy/systemd/container settings before activation. Keep database/inference listeners private and public routes on the single HTTPS origin.

## Activate and validate

Start database/inference, apply migrations, then start the API and worker. Check API schema readiness and actual model/sandbox qualification separately. Validate secure cookies, CSRF/Origin denial, outsider access denial, job completion, protected tests, distinct approvals and Git receipts through HTTPS. Switch the static release and proxy configuration only after preparation succeeds. Compare every deployed source/static/config byte with its local manifest. Preserve unrelated host services.

## Observe and respond

Monitor HTTPS, eligible errors/latency, pool saturation, queue age, worker liveness, disk/memory, model latency and lease/reconciliation failures. Limit log size, redact credentials/content and define retention. Inspect error-budget burn before risky changes. Record incidents and remediation; public status must not disclose private topology or credentials.

## Rollback

Keep the previous release, proxy/service configuration and encrypted database backup. Stop new admissions and let bounded work finish or cancel/reconcile it. Restore the previous frontend/API configuration and restart only project services. Database migrations are additive but schema compatibility must be checked; never blindly downgrade a database with accepted writes. If restoration is required, document lost-write scope against RPO, restore to an isolated database, verify rows/authorization, then reopen. Record actual RTO and final parity.

Account creation is operator-managed: `python -m app.manage create-user --email USER_EMAIL --name USER_NAME` prompts privately for a password. Use `--password-stdin` only with a protected pipe; never put passwords in arguments/history. Repository grants are operator CLI actions. See [self-hosting](self-hosting.md) and [disaster recovery](disaster-recovery.md).

Maintained by [Zahidul Islam](https://github.com/Zahidulislam2222). See the [documentation index](README.md) and [delivery roadmap](roadmap.md).

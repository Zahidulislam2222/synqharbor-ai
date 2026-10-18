# Contributing

Use an issue to describe a focused improvement, expected behavior and reproduction.
Keep credentials and private data out of public reports. Security findings use [private reporting](SECURITY.md).

1. Branch from current main and write acceptance criteria before implementation.
2. Keep copy and configuration in their central data/settings boundaries.
3. Run tests, types, lint, security scans and production build.
4. Exercise affected routes, keyboard flows, responsive states and reduced motion.
5. Request independent review and report actual evidence and remaining limits.

The lockfile is authoritative. Verify package versions, licenses and advisories.
Do not add paid services, tracking, provider keys or backend subsystems incidentally.
Preserve accessible semantic controls and current branding. Future architecture
belongs in the roadmap; never invent customer, capacity or compliance results.

Automated tests belong in tests/. Private recovery and personal tooling remain
ignored. Never bypass a security scan. Contributions use Apache 2.0.

## Backend contributions

Use Python 3.12 and the pinned `backend/requirements-dev.txt`. Run backend pytest, Ruff and mypy in addition to frontend checks. Changes to authorization, execution, migrations, release or configuration require acceptance criteria, meaningful regression coverage, security scans and fresh-context review. Do not run destructive database parity tests against application data. Real local-model/sandbox and deployed workflow checks supplement isolated automated tests. See [release acceptance](docs/release-checklist.md).

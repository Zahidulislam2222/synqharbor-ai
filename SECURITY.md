# Security policy

## Report privately

Use [GitHub private vulnerability reporting](https://github.com/Zahidulislam2222/synqharbor-ai/security/advisories/new).
This channel is enabled. Do not publish secrets, personal data or sensitive exploit
information in issues. Include affected release, reproduction, impact and mitigation.
The maintainer will investigate and coordinate disclosure; no bounty or fixed response
SLA is offered.

## Scope and support

The current release includes the frontend, authenticated control plane, durable worker, local inference and protected Python execution.
Maintained source, assets and project-specific serving configuration are in scope.
Do not access others' data, scan unrelated infrastructure, run denial-of-service
checks or attempt credential theft. A finding does not authorize broader testing.

Fixes target the latest 0.3.x release. Older releases should be upgraded after checks.
General connectors, arbitrary execution and distributed capacity remain roadmap capabilities. Test only explicitly authorized project surfaces.

Dependency review, Gitleaks, Semgrep, regression tests, browser checks and independent
review provide scoped evidence. They are not certification. See [security architecture](docs/security.md).

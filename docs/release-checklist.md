# Release acceptance checklist

- Confirm the authorized environment, Git author/repository, workload and spending boundary.
- Capture live files and compare the prior release manifest before edits.
- Keep credentials, private memory/recovery and operator documents out of Git.
- Run frontend/backend tests, type checks, lint, dependency audits, security scans and build.
- Obtain fresh-context review of source and deployment boundaries; retain verdict and limits.
- Validate migrations and least-privilege runtime identities on the intended database.
- Qualify actual local models and protected execution under the deployed service identity.
- Test HTTPS sessions, CSRF, outsider denial, both workflows, distinct approvals and release receipts.
- Verify restart persistence, encrypted backup and isolated restoration.
- Keep rollback artifacts; compare local/live source, static files and rendered settings.
- Push exact reviewed source under the maintainer identity; inspect hosted quality/security checks.
- Check documentation links, public overview, privacy/cookies, operating targets and roadmap consistency.
- Record measured limits, remaining gates and release identity. Review documentation when deployment behavior changes.

Maintained by [Zahidul Islam](https://github.com/Zahidulislam2222). See the [documentation index](README.md) and [delivery roadmap](roadmap.md).

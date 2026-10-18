# Privacy

Last reviewed: 2026-10-18.

SynqHarbor AI provides a public website and an operator-managed authenticated workspace. The maintainer is Zahidul Islam. Self-hosting operators determine their own deployment purposes and must publish the applicable operator contact and processing schedule before accepting customer personal data.

## Data and purposes

| Data | Purpose and destination |
|---|---|
| Account name, email, password hash and session | Authentication and account access in the application database |
| Memberships, tasks, messages, selected sources and artifacts | Requested collaboration and delivery; database and authorized local worker |
| Approval, audit, run and Git receipt records | Authorization, integrity, support and action reconciliation |
| Selected task/source/repository context | Installed local model inference on operator-controlled infrastructure |
| Technical request/security metadata | Hosting, delivery, abuse prevention and diagnostics |
| Browser-local workspace edits | Current `/workspace/` tab only; reload clears that interface state |

Passwords are hashed; plaintext passwords are not stored by the application. Source documents and candidate code can contain personal information, so users must provide only authorized, necessary content. The local model adapter sends no context to a paid/cloud inference endpoint. Model downloads and software updates contact their registries separately from task inference.

## Providers, retention and rights

The hosted website uses existing Contabo hosting and Cloudflare network delivery/security. GitHub hosts public source and feedback. Following third-party links uses those services under their own policies. Do not submit confidential or personal data in public issues.

Configured sessions/invitations expire after 24h by default. Operators control account/workspace retention, access and backup expiry. `SH_RETENTION_DAYS` expresses policy configuration; automatic deletion of all workspace records is not implemented. Operators must enforce and document deletion/retention operationally, including audit/legal holds and backup expiry. Technical log rotation currently bounds volume; a fixed age-based retention guarantee requires deployment verification.

Arrange a private channel through the [maintainer profile](https://github.com/Zahidulislam2222) for access, correction, export, deletion or privacy concerns. Verify the requester before disclosing data. Applicable rights, lawful basis, retention periods, processing locations and international transfers depend on the actual operator/customer arrangement. Do not enter regulated or sensitive customer data until that schedule and the required agreements/controls have been qualified.

See [data processing](data-processing.md), [legal readiness](legal-readiness.md) and [cookies](cookies.md). No advertising or behavioral analytics trackers are installed.

Maintained by [Zahidul Islam](https://github.com/Zahidulislam2222). See the [documentation index](README.md) and [delivery roadmap](roadmap.md).

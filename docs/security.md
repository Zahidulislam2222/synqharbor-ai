# Security architecture and threat model

## Implemented controls

Opaque server-side sessions, Argon2 password hashing, secure production cookies, session rotation/revocation, exact Origin and CSRF checks protect API mutations. Workspace membership and role authorization precede protected object access. Private API responses use `Cache-Control: no-store`; public caches must never store account or workspace responses.

Task revisions and artifact hashes bind approvals to exact content. Two distinct authorized accounts approve client and developer decisions. Repository execution requires an operator-created workspace/target/profile grant. Revoked members, sources, grants and stopped workspaces cannot authorize later publication. Agent instructions and retrieved documents never grant permissions.

The web service has no code execution route. Workers use pinned local model digests, structured responses, bounded correction rounds and separate review contexts. Protected test answers remain outside the model and guest. Rootless gVisor uses a read-only minimal rootfs, no guest network, no host credentials, fresh case processes and CPU/memory/process/output/time limits. Candidate output is untrusted data.

## Main threats and responses

| Threat | Control and verification |
|---|---|
| Guessed IDs and tenant crossover | Per-request membership/role checks and outsider denial tests |
| Session theft/CSRF | TLS, HttpOnly/Secure cookies, exact Origin, synchronizer token, revocation |
| Prompt injection or malicious source | Explicit source selection; source text cannot modify permissions or approval gates |
| Generated code escape/resource abuse | Isolated guest, private host boundary, bounded resources and negative probes |
| Stale review or concurrent Git writers | Revision/hash approval, expected-old-ref atomic comparison, native index lock |
| Worker retries and interrupted writes | Leases/fencing, intent ledger, idempotency and uncertain receipt reconciliation |
| Secret/dependency exposure | Ignored environment/recovery stores, public-source scans, pinned dependencies and CI audits |

## Operator requirements

Use least-privilege service accounts and database roles, pinned SSH host keys, private database/inference listeners, maintained TLS, bounded logs, verified encrypted backups and tested restoration. Do not expose Ollama, PostgreSQL, Docker sockets or runner state to the Internet. Keep runtime secrets outside source, browser bundles, logs and command arguments. Restrict operator access using MFA at the access provider where available; application administrator MFA remains a roadmap item.

Application-level authorization is implemented; PostgreSQL tenant RLS is a planned additional defense. Disk/volume encryption, independent penetration testing, supply-chain attestation, automated privacy erasure and continuous capacity testing require deployment-specific qualification. No scanner result establishes blanket security certification.

## Vulnerability handling

Use the private reporting route in [SECURITY.md](../SECURITY.md). Do not post credentials, personal information or exploit details in public issues. Assess impact, contain/revoke affected access, preserve redacted evidence, patch, verify and publish an appropriate advisory. Keep incident chronology and corrective actions.

References: [OWASP session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [multi-tenant security](https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html), [gVisor production guide](https://gvisor.dev/docs/user_guide/production/).

Maintained by [Zahidul Islam](https://github.com/Zahidulislam2222). See the [documentation index](README.md) and [delivery roadmap](roadmap.md).

# Backend deployment templates

Use these templates with a project-specific protected deployment configuration.
`services.compose.yaml` starts digest-pinned PostgreSQL 18 and local-only Ollama
with private host listeners, bounded resources and an internal Docker network.
Download and checksum-qualify the selected local model weights before removing
any temporary registry-download connectivity. Model inference needs no public
listener, cloud account or paid API key.

`service.unit.template` supervises separate unprivileged API and worker identities.
The API command is Uvicorn bound to loopback with proxy identity disabled; the
worker command is `python -m app.worker`. Keep runtime/migration secrets separate,
source root-owned, job/repository state worker-owned, and runtime environment files
readable only by the operator/service manager. The worker receives no Docker socket.

On supported Ubuntu hosts, `runsc.apparmor.template` allows user namespaces only
for the pinned runsc executable. Validate the sandbox under the actual worker
identity and service restrictions before enabling code jobs. This profile does
not replace the guest filesystem/network/resource restrictions.

Render settings with explicit values; unresolved placeholders must fail activation.
Before public activation, verify migrations, roles, inference, sandbox, HTTPS,
approvals, Git receipt integrity, restart and encrypted recovery. See
[operations](../../docs/operations.md), [self-hosting](../../docs/self-hosting.md)
and [release checklist](../../docs/release-checklist.md).

The internal Docker bridge intentionally has no outbound route. Native services
reach it through the bounded, dynamically unprivileged `proxy.socket.template`
and `proxy.service.template`, listening only on loopback. Static container
addresses derive from the validated project subnet. Docker does not publish ports
for this internal-only topology; the socket proxies supply that host boundary.
Keep temporary model-download networking disconnected after installation.
`deployment.py` validates centrally maintained deployment settings; use
`deployment.example.json` as a safe configuration example and inspect live
networks/routes before choosing a subnet.

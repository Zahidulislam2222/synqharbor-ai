# Core engine

The frontend and authenticated control plane implement two bounded core workflows:

1. Task, selected source documents and acceptance criteria → cited local AI draft → separate review → client
   approval → independent developer approval → recorded artifact delivery.
2. Operator-granted Python repository scope → proposed multi-file change → protected
   isolated tests → separate review → both human approvals → approved Git commit.

These workflows do not establish completion of the ten-phase production roadmap.
Unrestricted language/build environments, remote deployment connectors, production tenancy
qualification, cloud surfaces and capacity/recovery targets remain separate gates.

## Run locally

Install the pinned backend requirements into an isolated Python 3.12 environment.
Copy the backend settings from `.env.example` into `backend/.env`, supply a fresh
session secret and choose a database URL. Keep the real values in the ignored
recovery file. SQLite remains supported for development. PostgreSQL is exercised
by the full backend suite and the actual local qualification. Use separate migration and
runtime roles: runtime connections reject superuser, BYPASSRLS, schema-create and
table-owning privileges. The migration URL is used only by the explicit migration
command. PostgreSQL RLS policies and production operational qualification remain
separate roadmap work; restricted roles do not by themselves provide tenant RLS.

Build the frontend with the configured public origin and set
`SH_FRONTEND_DIRECTORY` to the resulting static export. From `backend/`:

```sh
python -m app.database
uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
# Separate terminal, same configured environment:
python -m app.worker
```

Open `/control/` on `SH_PUBLIC_ORIGIN`. Register the developer account, create a
workspace and invite a separate client account. Add explicit criteria before
starting a task. Read the exact artifact before approving. `/workspace/` remains
the browser-local workspace interface.

The control UI checks session identity around private refresh batches and hides
private state before rechecking a newly activated tab. This handles a shared
browser cookie changing in another tab. Keep the configured session request
budget compatible with the configured polling frequency; a regression checks the
defaults. Identity changes invalidate delayed responses and clear invitation,
artifact, CSRF and workspace state.

Release authorization and acknowledged workspace stops, member/source revocations
and host repository-grant changes share a database transaction lock. A control
change either completes before a new Git write and blocks it, or acknowledges
after the bounded in-flight Git operation ends. External inference still runs
outside transactions. Verification errors after an accepted Git commit retain an
uncertain receipt and the task reservation until read-only reconciliation proves
the outcome.

Git commits are prepared and verified in an isolated clone using the target's
effective installed hooks. Publication checks the expected old commit atomically;
the destination's native index lock coordinates ordinary Git writers during
installation. A rejected comparison never installs proposed working files. Target
repositories must be dedicated operator-owned working trees; manually editing
files or Git metadata during publication is outside this connector's contract.
After publication begins, incomplete checkout/index installation remains uncertain
and reserved for inspection and read-only reconciliation. Python entrypoints load
with their package context, including relative sibling imports.
Project imports retain their canonical names and shared state. The loader clears
overlapping cached modules and resolves approved roots before standard-library
packages; Python builtin/frozen module roots and import-loader infrastructure
names are reserved at profile validation. The harness retains its serializer
separately. Release receipts compare exact UTF-8 bytes, including line endings.

The API origin must match the browser origin exactly. Local HTTP uses a distinct
cookie name with secure cookies explicitly disabled; HTTPS deployments require
secure cookies and the appropriate host configuration. The API does not accept
arbitrary forwarded identity headers or cross-origin writes.

## Local inference and execution

Configure an already-installed loopback Ollama instance, model bindings and exact
installed model digests. `SH_CODE_BUILDER_MODEL` can specialize coding independently
of drafting. Cloud models, changed weights and unavailable models fail closed;
there is no paid-provider fallback or automatic model download. The optional curl
stdio bridge supports an inference service in a different local OS namespace.

Prompts and reviewed fixture definitions live in `backend/data/` and are validated
before use. Jobs snapshot the task inputs. Separate Builder/Reviewer contexts,
bounded correction rounds and exact content digests are persisted. Failed drafts
remain evidence; they never become an approved artifact automatically.

Coding needs a separately qualified gVisor runtime and minimal Python rootfs.
`backend/runner/prepare.py` prepares the currently supported Ubuntu Python runtime;
the operator supplies every runtime path through settings. Verify the downloaded
gVisor release checksum and retain its accompanying binaries. The rootfs contains
no home directory, cloud credentials, host mounts or protected expected answers.
Resource and output limits apply to each fresh isolated test invocation.

Repository profiles in `backend/data/repositories.json` define the allowed existing
Python source paths, callable entrypoint, specification and protected cases. Add a
profile through data, configure its target directory in `SH_REPOSITORY_TARGETS`,
then grant that exact scope to a workspace from the operator's host:

```sh
python -m app.manage grant-repository --workspace WORKSPACE_ID --target TARGET_ID --profile PROFILE_ID
python -m app.manage revoke-repository --workspace WORKSPACE_ID --target TARGET_ID --profile PROFILE_ID
```

The browser can list granted scopes but cannot grant itself access. Another
workspace cannot discover or submit the target. Changing its path, profile or
protected cases invalidates the grant and existing runs. Only approved paths enter
model context and the sandbox; no host clone credentials, `.git`, home directory or
test expectations are exposed. Standard-library Python modules can import each
other. Package installation, arbitrary shell commands, file creation/deletion and
general application hosting are outside this runner contract.

Fixture practice runs remain available and deliver an internal artifact. They no
longer implicitly receive a globally configured repository release target.

Clients can upload or paste small text/Markdown sources. Selected documents are
immutable snapshots with IDs, timestamps and hashes. Draft output must cite a
known selected ID; review and publication recheck current source access. Sources
are shared with workspace members and displayed as escaped text. Removal blocks
future dependent publication or release; already delivered documents cannot be
recalled from people who downloaded them.

Owners can stop/resume execution and revoke members. Stop cancels queued/running
work and blocks new submissions and releases; it cannot undo an external action
already accepted. All users can revoke their sessions. Every worker checkpoint
rechecks membership, stop state, task revision, sources and repository grants.

## Approvals and local release

For repository work the canonical artifact contains the complete approved file
map, base commit and scope hash. Evidence includes before/after hashes and diffs.
The release checks the clean original HEAD, stages only approved paths, invokes
normal security hooks, and verifies the commit parent, changed paths and every
committed/worktree byte. Changed heads block rather than overwrite newer work.

Two frozen Alembic revisions replace implicit table creation. A verified legacy
baseline can be adopted; type/index/foreign-key or unknown-table drift blocks
migration. Health reports a missing revision. Preserve a consistent backup before
upgrade; destructive downgrade is deliberately refused in favor of a verified
restore. Local qualification has an authenticated encrypted dump and isolated restore
verification; this is local recovery evidence, not an off-site availability SLA.

Human decisions bind an immutable artifact version and digest. Client approval
precedes developer approval, and the two decisions require different authorized
accounts. New versions cannot inherit old approvals. Pending or uncertain releases
reserve their task version until the outcome is resolved.

New submissions use explicitly granted `SH_REPOSITORY_TARGETS`. Submission
snapshots the approved source set and head. Delivery records intent before the
worker writes. The worker refuses a changed head, dirty tree, unsafe path or missing
security hook. A normal Git commit preserves the configured security checks,
then the receipt records commit, parent and exact file-hash evidence. The legacy
`SH_RELEASE_REPOSITORY` setting only supports historical single-file intents;
practice runs cannot create new implicit releases through it.

Delivery evidence can be downloaded as authenticated JSON from the control page.
It links the original request, immutable artifact hash, protected tests, independent
review, both human decisions and actual release receipt.

An interrupted outcome becomes uncertain. The reconciliation endpoint inspects
existing commit/digest evidence; it never blindly repeats the write. A failure or
uncertain receipt is visible in the control page. This connector does not deploy
SynqHarbor or any customer production application.

## Verification boundaries

Automated HTTP/security/regression tests use explicit test providers. Real local
model, gVisor, Git-hook and browser checks are separately retained as private
evidence. Static type/lint/security checks and the static frontend build are
separate gates. A local workflow pass does not prove model quality on arbitrary
tasks, hostile multi-tenant production safety, throughput or availability targets.

## Sandbox lifecycle and operator recovery

The gVisor bwrap personality ignores `--die-with-parent`. Killing its launcher
alone does not establish sandbox termination. The controller inventories only the
job-scoped OCI state, force-deletes any remaining sandbox, verifies an empty
inventory and then removes scratch data. Each cleanup command has the configured
`SH_RUNNER_CLEANUP_TIMEOUT` bound. If cleanup cannot be confirmed, private state is
retained with a recovery marker and further code jobs are refused until an operator
confirms deletion and clears that retained job. Drafting remains separately bounded.

Operators must verify zero remaining guest processes after CPU/output/timeout
failures under the actual service identity. See the official [gVisor process
lifetime behavior](https://gvisor.dev/docs/user_guide/personalities/bwrap/).

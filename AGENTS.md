# SynqHarbor-AI project instructions

The user's global rules remain authoritative. This file adds project context;
it does not replace, weaken, or duplicate the shared global instruction files.

## Current scope

The current release is the professional multipage static website, browser-local
workspace interface, public documentation and GitHub publication. Backend, account,
provider and execution capabilities remain roadmap work. Do not add a new subsystem
as an incidental website change. The build plan remains the future engineering roadmap.

Use the existing host for the authorized deployment. New service charges are not
part of this release. Verify live drift, capacity and the intended scope first.
Keep private recovery records, infrastructure access information and local memory
out of public files and command output.

## Session start and private records

- Read memory/MEMORY.md, relevant indexed notes, and PROJECT-DOSSIER.md.
- Keep all project memory inside memory/; MEMORY.md is an index only.
- Verify Git ignores CREDENTIALS.md, PROJECT-DOSSIER.md, and memory/ before writing.
- Record actual project secrets only in approved environment/storage and the ignored
  CREDENTIALS.md recovery file. Never print secrets in output or chat.
- Update the dossier after notable decisions, verification, fixes, and milestones.
  Preserve existing incident entries; do not invent evidence or incidents.
- Personal scripts belong in ignored manual-tests/ and must never be deleted.
  Keep the future real automated CI suite tracked in a separate directory.

## Implementation gates

- Research the approach, define acceptance criteria, and identify configuration
  ownership before implementing. Use one central typed settings boundary, safe
  .env.example entries, and validated content files after the stack is selected.
- Keep edit scanning and commit scanning enabled. See README.md for the active
  WSL security commands; .pre-commit-config.yaml owns tool configuration.
- Report tests, types, lint, security scans, build, real-flow verification, and
  fresh-context review separately. A missing gate must be stated explicitly.
- Add escaped defects to DEFECT-LOG.md with the gate that should have caught them.
- After a GitHub remote is added, install and verify the machine security CI
  template; leave paid AI review disabled unless explicitly approved.
- For production work, first capture and compare live files, edit locally, verify,
  deploy only within authorization, then prove file parity.
- Stop and give the global-rule money warning before any chargeable action.
- Keep my-project-view/ locked unless the user explicitly requests this project's
  Google Doc update; then update the same Doc and verify its refreshed local PDF.

## Agent memory

Codex: use this project's memory/ explicitly; never write project memory to a
global agent store. Claude: .claude/settings.local.json points auto memory here
for WSL. Before native Windows Claude use, update that ignored setting to the
absolute Windows path for this same memory folder and verify it loads.

<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

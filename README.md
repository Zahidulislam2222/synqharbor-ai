# SynqHarbor AI

**One workspace. Human-led. Agent-powered.**

A self-hostable collaboration product for clients, developers and business teams,
maintained by **[Zahidul Islam](https://github.com/Zahidulislam2222)**.

[Website](https://synqharbor.zahidul-islam.com/) · [Workspace](https://synqharbor.zahidul-islam.com/workspace/) · [Documentation](https://synqharbor.zahidul-islam.com/docs/) · [Roadmap](https://synqharbor.zahidul-islam.com/roadmap/)

![SynqHarbor harbor artwork](public/media/harbor.webp)

## Available capabilities

- Professional product, company, engineering, security and legal pages.
- Workspace views for tasks, conversations, agents, artifacts, approvals, knowledge, activity and preferences.
- Browser-tab-local task creation, search, filters, status changes, version-aware approval interactions, messages and report downloads.
- Responsive layouts, self-hosted fonts, Motion, progressive smooth scrolling, reduced-motion support and a silent ambient hero loop.
- Static builds, automated regression checks, security scanning and portable deployment.

Workspace state lives in the current browser tab and resets on reload. Authentication,
server persistence, collaboration APIs, agent execution and external actions remain
future engineering milestones. No provider subscription is connected by the website.

## Run locally

Use **Node.js 24 LTS** and npm. Copy `.env.example` to `.env.local` and set the public
origin. Never place a credential in a public-prefixed variable.

```bash
npm ci
npm run dev
```

```bash
npm test
npm run typecheck
npm run lint
npm run build
```

The production build creates `out/`. Serve it over HTTPS with a static web server.
See [self-hosting](docs/self-hosting.md) and [serving templates](infra/README.md).

## Engineering documentation

Start with the [documentation index](docs/README.md) or [technical overview](docs/technical-overview.md).

| Topic | Guide |
|---|---|
| Components and trust boundaries | [Architecture](docs/architecture.md) |
| Persistent platform development | [API roadmap](docs/api.md) |
| Security and reporting | [Security architecture](docs/security.md), [SECURITY.md](SECURITY.md) |
| Legal and data responsibilities | [Privacy](docs/privacy.md), [terms](docs/terms.md), [data processing](docs/data-processing.md) |
| Reliability and recovery | [Objectives](docs/reliability.md), [disaster recovery](docs/disaster-recovery.md) |
| Future 1M+ concurrent-user qualification | [Scalability](docs/scalability.md), [performance tests](docs/performance-testing.md) |
| Startup free-cloud boundaries | [AWS/GCP/Azure cost plan](docs/cloud-costs.md) |
| Phased implementation | [Roadmap](docs/roadmap.md), [full ten-phase plan](BUILD-PLAN.md) |
| Accessible interaction | [Accessibility](docs/accessibility.md) |

The initial **99% availability objective** and future **1M+ simultaneous-user envelope**
are engineering targets. Assumptions, qualification gates and funding requirements
are documented separately from current behavior.

## Stack and structure

Next.js 16, React 19, TypeScript, Motion, Lenis and Lucide. Fonts and media are
self-hosted. FastAPI/PostgreSQL belong to the planned application architecture.

```text
src/app/          Static routes, metadata, sitemap and robots
src/components/   Website and workspace interface
src/config/       Typed public configuration
src/content/      Maintained copy, navigation and workspace content
public/           Self-hosted media and public assets
tests/            Automated regression tests
docs/             Public technical and policy documentation
infra/            Portable static-serving templates
.github/          Public-repository CI and contribution templates
```

## Contributing and support

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
Issues accept reproducible non-sensitive defects and documentation feedback.
Vulnerabilities use the private channel in [SECURITY.md](SECURITY.md).
Community support has no contracted response-time SLA.

## License and publication

Source is [Apache 2.0](LICENSE). Dependencies and typefaces retain their own licenses;
see [third-party notices](THIRD-PARTY-NOTICES.md). Credentials, private recovery records,
local memory and unshipped work are excluded. No production access material is
needed to build the website.

# Data processing and operator responsibilities

## Processing schedule before customer data

Each deployment must identify the actual controller, processor and subprocessors; user/customer locations; account and content data categories; processing purposes and lawful basis; sensitive-data conditions; hosting/support/model locations; retention/deletion; transfer mechanisms; and accountable contacts. A software license is not a signed processing agreement.

| Surface | Current boundary | Required operator evidence |
|---|---|---|
| Accounts and sessions | Database-backed access and revocation | Identity recovery, request verification, retention and privacy notice |
| Workspace content | Membership/role-scoped API and worker context | Customer authority, minimization, access review and tenant tests |
| Model inference | Installed local weights; task-selected context | Local processing location, model license, prompts/log retention and authorized access |
| Code execution | Isolated protected test cases | Host/sandbox qualification, abuse controls and incident handling |
| External Git write | Operator-granted dedicated repository | Explicit destination authority, exact approval and receipt reconciliation |
| Hosting/CDN | Technical request processing | Vendor terms, subprocessors, location/transfer and log controls |
| Backups | Operator-controlled encrypted archives | Key separation, retention, restoration and eventual expiry |

## Rights and deletion

Provide a verified private request channel, export useful account/workspace data without exposing another tenant, correct inaccurate data and enforce applicable deletion/restriction/objection rights. Preserve narrowly justified legal holds. Explain that deletion from active systems and expiry from backups follow different schedules. Restoration must reapply deletion/revocation obligations before reopening service. Automatic comprehensive erasure is roadmap work; operator procedures must cover present deployments.

## Incident and transfer obligations

Maintain detection, containment, evidence preservation, notification decision and recovery procedures. Under GDPR, processor-to-controller notification differs from the conditional controller-to-authority 72-hour requirement. Assess international transfers and vendor support access; server geography alone does not resolve jurisdiction. Regulated health data requires a separate eligibility, contract and control review before any processing.

Primary guidance: [EDPB roles](https://www.edpb.europa.eu/sme/learn-the-basics/data-controller-or-data-processor_en), [data security](https://www.edpb.europa.eu/sme/be-compliant/secure-personal-data_en), [HHS cloud guidance](https://www.hhs.gov/hipaa/for-professionals/special-topics/health-information-technology/cloud-computing/index.html).

Maintained by [Zahidul Islam](https://github.com/Zahidulislam2222). See the [documentation index](README.md) and [delivery roadmap](roadmap.md).

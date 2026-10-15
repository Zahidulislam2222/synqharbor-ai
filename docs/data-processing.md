# Data processing and deployment responsibilities

The current website has no deployed account API, contact intake form or remote
workspace database. Workspace interactions use browser-tab memory. Hosting/network
providers can process technical request metadata as described in the privacy policy.

| Data class | Current behavior | Future requirement |
|---|---|---|
| Workspace edits | Current browser tab only | Authenticated tenant storage, exports, deletion and retention |
| Account details | No account registration | Identity verification/recovery and documented lawful processing |
| Contact messages | Linked services handle communication | Private intake, retention and verified receipt states |
| Request logs | Infrastructure-controlled technical logs | Minimization, documented duration and rights handling |
| Model context | No inference requests | Explicit provider/data destination qualification and disclosure |

## Roles and processing schedule

A self-hosting operator determines deployment purposes and controls stored data.
The software maintainer does not automatically become a processor for every
installation. Hosted service contracts must identify the actual controller,
processor, subprocessors, categories, purposes, locations, retention and safeguards.
No signed DPA is supplied by this website.

Before a customer deployment accepts personal data, complete the processing
schedule, operator contact, rights-request process, breach process and international
transfer assessment. Do not infer governing law from a timezone or server location.

## Export, deletion and incident handling

Future deletion must cover databases, indexes, objects, caches and backup expiry.
Legal holds and backup restoration behavior need explicit policies. Export must
preserve useful provenance without exposing another tenant’s information.

Where GDPR applies, distinguish processor notification to its controller from
conditional controller notification to an authority. Do not treat a conditional
72-hour rule as a universal incident promise.

Primary guidance: [EDPB SME guide](https://www.edpb.europa.eu/sme_en),
[individual rights](https://www.edpb.europa.eu/sme/be-compliant/respect-individuals-rights_en),
[transfers](https://www.edpb.europa.eu/sme/be-compliant/international-data-transfers_en),
[breaches](https://www.edpb.europa.eu/sme/assess-the-risks/data-breaches_en).

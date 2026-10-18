# Cloud roles and cost boundaries

The startup goal is zero new service charges, using an existing server within
measured capacity. Existing infrastructure still has ownership and traffic costs.
The million-user target requires a separately funded, qualified operating stage.

| Platform | Planned bounded role | Qualification and limits |
|---|---|---|
| AWS | Public immutable assets | CloudFront Free flat-rate is distinct from pay-as-you-go allowances; published plan1M monthly requests/100GB transfer/5GB included storage, no SLA |
| GCP | Public operator documentation | Firebase Spark, no billing link; quota exhaustion can stop the affected service; linking billing upgrades to Blaze |
| Azure | Public static reference surface | Static Web Apps Free, published250MB/app and two custom domains; no SLA; intended for personal projects |
| Existing host | Current website, API, worker and local inference | Inspect actual capacity, traffic allowance, private networking and restore readiness |

No AWS, GCP or Azure deployment is claimed by this release. Account
eligibility, current limits, region support and all dependencies must be checked
before activation. The three clouds must not become competing task authorities.

One million initial 1MB page loads already require approximately 1TB of edge transfer.
Startup free plans do not supply the full target workload. Metered inference,
managed databases, log storage, egress, domains and added origin resources can be
separately chargeable even when another service is free.

Budgets/alerts are not universal hard spending caps. Every paid stage requires a
current workload-based estimate and explicit approval before provisioning. Do not
use expiring credits as the production foundation or enable an automatic paid fallback.

Checked against primary provider documentation on 2026-10-16:
[AWS pricing](https://aws.amazon.com/cloudfront/pricing/),
[Firebase plans](https://firebase.google.com/docs/projects/billing/firebase-pricing-plans),
[Azure plans](https://learn.microsoft.com/en-us/azure/static-web-apps/plans).

## Cloud-first growth and hybrid placement

The architecture roadmap prioritizes AWS, GCP and Azure experience through suitable
components within verified free allowances. The existing host is the authorized
current release target and supplies heavy local inference and protected execution;
future cloud components require their own account, allowance, isolation and rollout
qualification. This preference does not trigger migration or billing activation.

Keep public immutable delivery, frontend distribution and appropriate stateless
components in the selected clouds. Evaluate the already-planned AWS public asset
edge, Firebase Spark documentation delivery and Azure Static Web Apps frontend
surface first. Preserve one task/approval authority and avoid three competing
account databases. For control-plane expansion, qualify serverless compute,
database connectivity, queues, identity, egress and observability together; a free
compute allowance alone does not establish a free application stack.

Before exceeding an allowance, compare a hybrid arrangement that retains cloud
surfaces while keeping costly models, isolated execution and other suitable heavy
work on bounded existing hardware. Secure the cross-environment boundary with
workload identity, encrypted transport, narrow authorization and explicit latency,
quota and residency budgets. The current loopback-only model adapter requires a
reviewed distributed adapter before remote inference is supported. Keep paid
capacity disabled until its workload-based cost and authorization are established.

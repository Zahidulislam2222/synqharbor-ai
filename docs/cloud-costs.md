# Cloud roles and cost boundaries

The startup goal is zero new service charges, using an existing server within
measured capacity. Existing infrastructure still has ownership and traffic costs.
The million-user target requires a separately funded, qualified operating stage.

| Platform | Planned bounded role | Qualification and limits |
|---|---|---|
| AWS | Public immutable assets | CloudFront Free flat-rate is distinct from pay-as-you-go allowances; published plan1M monthly requests/100GB transfer/5GB included storage, no SLA |
| GCP | Public operator documentation | Firebase Spark, no billing link; quota exhaustion can stop the affected service; linking billing upgrades to Blaze |
| Azure | Public static reference surface | Static Web Apps Free, published250MB/app and two custom domains; no SLA; intended for personal projects |
| Existing host | Initial website and future core | Inspect actual capacity, traffic allowance, private networking and restore readiness |

No AWS, GCP or Azure deployment is claimed by this website release. Account
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

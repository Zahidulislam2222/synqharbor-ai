# Security architecture

The authenticated phase requires secure server-side sessions, revocation, exact Origin checks, CSRF protection and explicit membership authorization before any object reaches the caller.

## Identity and tenant boundaries

The authenticated phase requires secure server-side sessions, revocation, exact Origin checks, CSRF protection and explicit membership authorization before any object reaches the caller.

## Artifacts and consequential actions

Approvals bind the exact version/hash, destination and arguments. A content change invalidates authorization. Separate actors approve content and release. External writes record intent, idempotency keys and destination receipts.

## Execution and retrieval

Apply permissions before retrieval content reaches a model. Treat retrieved instructions as untrusted. Isolate runners and generated applications, restrict network/filesystem access, and keep provider credentials outside browser code.

See [the documentation index](README.md) and [the full build plan](../BUILD-PLAN.md).

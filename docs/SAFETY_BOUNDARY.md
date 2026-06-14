# ActionRail Finance — Safety Boundary

This document states what ActionRail does, what it deliberately does not do, and what is required before any real finance use.

---

## What ActionRail does

ActionRail Finance is a **transaction runtime for finance AI agents**. For each risky finance action it:

1. Accepts a structured preflight request (intent, action, invoice payload, evidence).
2. Runs deterministic policy checks (vendor, duplicate, contract, amount, evidence, intent lock).
3. Returns a machine-readable decision: `allow`, `approval_required`, `blocked`, or `needs_more_evidence`.
4. Gates human approval when required — approval and execution are separate steps.
5. Simulates execution in this MVP and produces an **HMAC-SHA256 signed receipt** over canonical JSON.
6. Optionally creates **local accounting sandbox** draft bill and audit packet JSON after execution — files on disk only, no external mutation.

The primary interface is the HTTP API. The dashboard is for human review and demos.

---

## What ActionRail does not do

This MVP explicitly does **not**:

- Execute real bank transfers or payment-rail transactions.
- Post to QuickBooks, Xero, Zoho, Tally, or any live ERP/ledger.
- Connect to Gmail, Outlook, or external email ingestion.
- Call Stripe, Razorpay, or payment processors.
- Provide production authentication, RBAC, or multi-tenant isolation.
- Guarantee OCR accuracy — extraction assists review; humans confirm before transaction creation.
- Replace your accounting system, AP workflow, or compliance program.

Every execution response and signed receipt includes an explicit demo boundary message.

---

## Why execution is simulated

Real payment and ledger mutation requires:

- Production credentials and secret management.
- Provider sandbox certification and rollback plans.
- Legal and compliance review.
- Audit-grade logging and monitoring.
- Human accountability chains beyond a demo approver ID.

Simulated execution lets the MVP prove the **full transaction primitive** — preflight, decision, approval gate, execution boundary, signed receipt — without risking real money or corrupting external systems.

This is a codified decision (see `DECISIONS.md` D3). Do not bypass it without an explicit new decision entry.

---

## Why receipt signing matters

Finance actions need tamper-evident proof. The signed receipt binds:

- Transaction identity and decision at preflight.
- Checks run and their outcomes.
- Approval record (who, when).
- Execution timestamp and demo boundary statement.

If any field in the canonical payload changes, the HMAC signature no longer verifies. This is the audit primitive agents and controllers can rely on before trusting an automated action.

Receipt payload semantics are stable in this MVP — writeback metadata is intentionally **not** included in the signed payload.

---

## Why local accounting sandbox writeback is safe

The accounting sandbox adapter:

- Writes JSON files to `data/accounting_sandbox/` on the local machine.
- Makes **zero external API calls**.
- Uses `local://accounting_sandbox/...` references in the UI — no absolute paths exposed.
- Is idempotent — re-clicking does not create duplicate writebacks.
- Carries an explicit safety note: *Local sandbox only. No ERP, bank, or ledger mutation performed.*

It demonstrates **integration readiness** — the shape of a future QuickBooks/Xero adapter — without pretending to be one.

---

## Why uploaded files are stored locally

Invoice uploads go to `data/uploads/` on disk:

- No cloud upload in this MVP.
- SHA-256 hash stored for integrity reference.
- Evidence referenced as `local://uploaded_documents/{id}` in transaction payload.
- Files are gitignored — never commit real customer invoices.

Local storage keeps the demo self-contained and avoids accidental data leakage to third parties.

---

## No external mutation guarantee

In this codebase, no route or adapter:

- Sends HTTP requests to bank, ERP, accounting, or payment APIs.
- Reads OAuth tokens for external finance services.
- Writes to external ledgers or databases.

If you add real integrations, that requires a new phase, new tests, new decision entries, and the production requirements below.

---

## Production requirements before real finance use

Do **not** use this MVP for production finance automation without addressing:

| Requirement | Why |
|---|---|
| **Authentication / RBAC** | Know who approved, who executed, tenant isolation |
| **Audit-grade storage** | Immutable logs, retention policy, backup/restore |
| **Secret management** | HMAC keys, provider credentials — not in repo or env files alone |
| **Provider sandbox review** | Certified connectors for each ERP/bank with rollback |
| **Approval policy admin** | Configurable thresholds, chains, delegation — not seed JSON only |
| **Monitoring & alerting** | Failed executions, policy drift, anomalous agent behavior |
| **Legal / compliance review** | Jurisdiction, data handling, SOX/audit requirements |

This MVP is a **local execution-control prototype**. It proves the primitive. Production finance automation is a separate engineering and compliance program.

---

## Related documents

- [`DECISIONS.md`](../DECISIONS.md) — architectural why-decisions
- [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) — system design
- [`docs/PROJECT_COMPLETION.md`](PROJECT_COMPLETION.md) — MVP completion status
- [`README.md`](../README.md) — quickstart and scope

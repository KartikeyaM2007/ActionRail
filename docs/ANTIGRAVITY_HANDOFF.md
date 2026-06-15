# ActionRail Finance — Antigravity Handoff

## Current status
Local production-grade prototype for finance agent execution control. 196 tests passing.

## Product one-liner
ActionRail turns risky finance agent actions into safe, auditable transactions.

## What the project is
A local execution control rail for AI agents. Agents propose transactions; ActionRail validates, gates, and returns a signed receipt only after human review or policy clearance.

## What the project is not
- It does not integrate with real payment rails (no Stripe/Razorpay).
- It does not mutate live ERPs or banks.
- It does not have live OAuth or multi-tenant SAAS features.
- All execution is simulated locally.

## Core safety boundary
Execution is simulated. The system is designed to provide a sandbox where agent actions are converted into a reviewable `transaction` record. A cryptographic receipt is issued upon execution, but no real money moves.

## Current feature map
- FastAPI backend + SQLite store
- Jinja2 server-rendered neo-brutalist dashboard
- Local auth, login, RBAC
- CSRF-protected dashboard forms
- Transaction lifecycle (preflight, lock, approval, execution)
- Audited admin control plane (vendors, contracts, policies)
- Real invoice upload + optional OCR
- Accounting sandbox writeback
- JSON API (byte-identical)

## Architecture summary
A FastAPI app wrapping an SQLite database. Agents interact via a JSON API to `preflight` and `execute` transactions. Human users interact via a server-rendered dashboard to `approve` or `reject` them. Core logic lives in `app/policy.py` and `app/store.py`.

## Key modules and responsibilities
- `app/main.py`: Route definitions (JSON + HTML).
- `app/policy.py`: Core business rules, validation, preflight checks, receipt signing.
- `app/store.py`: SQLite connection, queries, data access layer.
- `app/models.py`: Pydantic schemas.
- `app/control.py` & `app/auth.py`: Authentication, RBAC, CSRF, audit ledger.
- `app/admin_routes.py`: Admin dashboard routes.
- `app/extraction.py` & `app/ocr.py`: Document processing.
- `app/accounting.py`: Simulated ledger writeback.

## Database tables summary
- `users`: Local dashboard user accounts.
- `audit_events`: Immutable audit ledger.
- `vendors`: Onboarded vendors.
- `contracts`: Registered contracts with limits and terms.
- `policies`: Global configuration and thresholds (e.g., `finance_default`).
- `uploaded_documents`: Metadata and hashes of user uploads.
- `transactions`: The core state machine of proposed actions.
- `intent_locks`: Idempotency keys to block concurrent identical requests.
- `accounting_writebacks`: Sandbox ledger records.
- `contract_evidence`: Uploaded files serving as contract proof.
- `invoices`: Extracted/simulated invoice records.

## Auth, RBAC, and CSRF summary
Local cookie-based session auth (`app/auth.py`). Roles (`admin`, `controller`, `auditor`, `agent`, etc.) map to permissions (e.g., `approve_transaction`, `execute_transaction`, `manage_admin`). Dashboard forms require CSRF tokens mapped to user session and target action.

## Admin control plane summary
`/dashboard/admin` routes allow managing `vendors`, `contracts`, `contract_evidence`, and `policies`. All state changes (e.g., vendor verified, contract activated) create `audit_events`.

## Policy engine summary
`run_preflight()` validates constraints, checks for duplicates via `intent_locks` and recent invoices, evaluates against `finance_default` thresholds, and computes a decision: `allow`, `approval_required`, `needs_more_evidence`, or `blocked`.

## Invoice upload / OCR / review flow
Users upload a PDF/image (`/dashboard/invoices/upload`). `app/extraction.py` runs `pypdf` text extraction and regex; `app/ocr.py` runs Tesseract if installed. Results populate a review screen before creating a preflighted transaction.

## Transaction lifecycle
1. Proposed by agent/user -> `preflighted`
2. Evaluated -> Decision is `allow`, `approval_required`, etc.
3. If `approval_required` -> Human review -> `approved` or `rejected`
4. If `approved` or `allow` -> `execute`
5. Status becomes `executed` -> Receipt signed.

## Receipt signing
HMAC-SHA256 signature using `ACTIONRAIL_SECRET_KEY` on the transaction payload to prove the action cleared the rail.

## Accounting sandbox writeback
Post-execution, users can generate a simulated draft bill in a local accounting adapter (`app/accounting.py`), creating an `accounting_writebacks` record.

## Audit ledger
All control plane actions, auth events, and manual approvals generate structured JSON records in `audit_events`. Displayed at `/dashboard/audit`.

## Demo users and roles
- Admin (admin)
- Finance Controller (controller)
- Agent Runner (agent)
- Auditor (auditor)

## Local-only files and ignored directories
- `actionrail.db`
- `data/uploads/`
- `data/contract_evidence/`
- `data/accounting_sandbox/`
- `data/datasets/`
- `kaggle/`

## Existing tests and what they cover
196 tests covering policy logic, dashboard routing, auth, CSRF, admin control plane, OCR extraction, file uploads, dataset scripts, safety guards, accounting writeback, and JSON API shape preservation.

## Current known limitations
- Local SQLite only; no Postgres.
- Hardcoded `finance_default` policy key.
- Demo auth (password hashes, but no 2FA or external SSO).
- No actual integrations (Stripe, Xero, etc).

## Non-negotiable constraints
- Keep execution simulated only.
- Do not add external integrations (banks, ERP).
- Do not refactor production code.
- Do not change API JSON response shapes.
- Do not change receipt signature payload.

## Safe future work
- Dashboard UI polish (CSS/Jinja2).
- Extended test coverage.
- New local-only sandbox integrations.

## Dangerous future work to avoid
- Mutating live production state.
- Real API calls to external services for payment execution.

## Next planned phase
Phase 5C: approval workflow engine, maker-checker controls, and separation of duties.

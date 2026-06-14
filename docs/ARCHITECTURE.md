# ActionRail Finance — Architecture

Readable overview for GitHub reviewers, interviewers, and the next developer picking up the repo.

---

## High-level architecture

```text
┌─────────────────┐     HTTP/JSON      ┌──────────────────────────────┐
│  Finance AI     │ ─────────────────► │  FastAPI (app/main.py)       │
│  Agent / CLI    │ ◄───────────────── │  Routes orchestrate only     │
└─────────────────┘                    └──────────────┬───────────────┘
                                                      │
                    ┌─────────────────────────────────┼─────────────────────────┐
                    ▼                                 ▼                         ▼
            ┌───────────────┐               ┌─────────────────┐         ┌──────────────┐
            │ app/policy.py │               │  app/store.py   │         │ Jinja2 HTML  │
            │ Preflight     │               │  SQLite         │         │ dashboard    │
            │ Receipt sign  │               │  Seed data      │         │ (secondary)  │
            └───────────────┘               └─────────────────┘         └──────────────┘
                    │                                 │
                    │                                 ├── data/uploads/ (local files)
                    │                                 └── data/accounting_sandbox/ (local JSON)
                    ▼
            ┌───────────────┐
            │ app/extraction│  PDF text + regex fields
            │ app/ocr.py    │  Optional Tesseract OCR
            │ app/accounting│  Local sandbox writeback adapter
            └───────────────┘
```

**Principle:** Business rules live in `app/policy.py` and `app/store.py`. Route handlers and templates orchestrate — they do not decide.

---

## Request flow

### Agent API (primary)

1. `POST /actions/preflight` — agent submits intent + invoice payload.
2. Policy engine runs checks → returns decision + transaction ID.
3. If `approval_required`, human calls `POST /approvals/{id}/approve` or rejects.
4. If executable, agent or human calls `POST /actions/{id}/execute`.
5. `GET /receipts/{id}` — signed HMAC receipt over canonical JSON.

### Dashboard (secondary, same backend)

Server-rendered HTML forms POST to dashboard routes that call the same internal helpers as the JSON API. `303 See Other` redirects after every state change.

**Phase 5A control plane (local demo):**

- Session auth via Starlette `SessionMiddleware` (`ACTIONRAIL_SESSION_SECRET`; dev fallback documented in code).
- Six demo roles with RBAC on dashboard actions (`app/auth.py`, `app/control.py`).
- CSRF tokens on all dashboard POST forms.
- Audit ledger (`audit_events` table) with `/dashboard/audit` for auditor/admin.
- Transaction-level audit trail on detail pages.

JSON API routes remain unauthenticated in this phase — agent integrations unchanged.

---

## Transaction lifecycle

```text
preflighted → approved → executed
     │            │
     ├─ rejected (terminal)
     ├─ blocked (terminal)
     └─ needs_more_evidence (may retry with evidence)
```

**Preflight decision** is historical — what policy returned at preflight time.

**Status** is current — where the transaction is in the lifecycle now.

An executed transaction may still show `preflight decision = approval_required` because that was the original policy outcome.

---

## Data model summary (SQLite)

| Table / area | Purpose |
|---|---|
| `transactions` | Core transaction record: intent, action, invoice JSON, decision, risk, status, checks, approval, execution, receipt |
| `vendors`, `contracts`, `invoices`, `policies` | Seed reference data for demo policy checks |
| `intent_locks` | Prevents concurrent agent work on same invoice intent |
| `uploaded_documents` | Local invoice files + extraction/OCR metadata |
| `accounting_writebacks` | Writeback metadata (idempotent per transaction + provider) |

Local files:

- `data/uploads/` — uploaded invoice PDFs/images (gitignored).
- `data/accounting_sandbox/draft_bills/` — draft bill JSON (gitignored).
- `data/accounting_sandbox/audit_packets/` — audit packet JSON (gitignored).

---

## Policy engine summary

`run_preflight()` in `app/policy.py` runs seven checks:

| Check | Purpose |
|---|---|
| `action_allowed` | Action in vendor's allowed actions |
| `vendor_verified` | Vendor exists in registry |
| `duplicate_invoice` | Same vendor + amount within window |
| `contract_match` | Contract required above threshold |
| `amount_policy` | Approval / critical amount thresholds |
| `evidence_attached` | Evidence URLs present when required |
| `intent_lock` | No conflicting in-flight intent |

Returns one of: `allow`, `approval_required`, `blocked`, `needs_more_evidence`.

---

## Upload / OCR / review summary

Two-step flow — upload never creates a transaction directly:

1. **Upload** (`POST /dashboard/invoices/upload`) — store file, extract PDF text or run optional OCR, save `uploaded_documents` row.
2. **Review** (`GET/POST .../review/{doc_id}`) — human confirms/edits fields.
3. **Submit** — builds preflight payload with `local://uploaded_documents/{id}` evidence reference → `run_preflight()`.

Extraction is conservative: low-confidence amounts require manual entry.

---

## Receipt signing summary

On execution, `sign_receipt()` in `app/policy.py`:

- Builds canonical JSON payload (transaction, decision, checks, approval, execution timestamp).
- Signs with HMAC-SHA256 using server secret.
- Stores receipt on transaction; returns via `GET /receipts/{id}`.

Receipt semantics are stable — do not add writeback metadata to signed payload without a new decision entry.

---

## Accounting sandbox writeback summary

After `status = executed`:

- `LocalAccountingSandboxAdapter` in `app/accounting.py` writes draft bill + audit packet JSON locally.
- No external API calls.
- Idempotent: same transaction + provider returns existing writeback.
- UI shows `local://accounting_sandbox/...` references, not absolute paths.

---

## What is local-only (this MVP)

| Component | Local-only behavior |
|---|---|
| Execution | Simulated — no bank/ERP mutation |
| Database | SQLite file on disk |
| Uploads | Files in `data/uploads/` |
| OCR | Optional local Tesseract |
| Accounting writeback | JSON files in `data/accounting_sandbox/` |
| Auth | None — demo/dev only |

---

## What would change in production

| Area | MVP today | Production direction |
|---|---|---|
| Execution | Simulated response | Provider connectors with sandbox → prod promotion |
| Storage | SQLite | Postgres + object storage (S3/GCS) |
| Auth | Open API | OAuth2/API keys, RBAC, tenant isolation |
| Secrets | Env var HMAC key | Secret manager (Vault, AWS SM) |
| OCR | Local Tesseract | Managed OCR or vendor API with confidence SLAs |
| Writeback | Local JSON files | QuickBooks/Xero/Tally sandbox APIs with audit |
| Monitoring | None | Structured logs, metrics, alerting |
| Compliance | Not reviewed | Legal/compliance sign-off before real finance use |

See [`docs/SAFETY_BOUNDARY.md`](SAFETY_BOUNDARY.md) for the full production requirements list.

---

## Key files

| Path | Role |
|---|---|
| `app/main.py` | FastAPI routes, dashboard orchestration |
| `app/policy.py` | Preflight, approval guards, execution, receipt signing |
| `app/store.py` | SQLite schema, queries, seed data |
| `app/models.py` | Pydantic request/response schemas |
| `app/accounting.py` | Sandbox writeback adapter |
| `app/extraction.py` | PDF text + regex field extraction |
| `app/ocr.py` | Optional image OCR |
| `tests/` | 154+ pytest tests |

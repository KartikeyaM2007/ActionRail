# ActionRail Finance

> **Transaction runtime for finance AI agent actions.**

ActionRail sits between AI finance agents and the finance systems they touch. Before an agent approves an invoice, executes a payment, posts a journal entry, or submits a reconciliation, ActionRail runs the checks, enforces policy, gates approval, and generates a signed receipt — without the agent ever mutating a system of record directly.

---

## What it is

Finance AI agents need more than a prompt and a tool call. They need a **transaction rail**: a layer that enforces evidence requirements, runs policy checks, acquires intent locks, routes approvals, controls execution timing, and produces tamper-evident receipts.

ActionRail is that rail. It is **infrastructure**, not an approval dashboard. The primary surface is an HTTP API an agent calls. The dashboard exists so humans can review, approve, and demo — it is not the product.

Every meaningful agent action becomes a transaction with an explicit lifecycle:

```text
preflight → decision → approval (if required) → execute → signed receipt
```

The agent calls `POST /actions/preflight` and receives one of four machine-readable decisions:

| Decision | Meaning |
|---|---|
| `allow` | Passes all checks. Agent may proceed. |
| `approval_required` | Passes checks but needs human sign-off before execution. |
| `blocked` | A check failed (duplicate, unknown vendor, etc.). Agent must not proceed. |
| `needs_more_evidence` | Evidence or contract reference is missing. Agent must attach before retrying. |

These decisions are structural. An agent integrates with them the same way it integrates with an API status code.

## Why it exists

AI agents are starting to perform real finance work. When that work is wired as raw tool calls, the results are dangerous:

- A duplicate invoice goes out the door because no check ran.
- A payment executes without approval because the policy lived in a prompt.
- An audit trail is missing because nothing generated a receipt.
- Two agents conflict because no intent lock exists.

Finance teams already have controls — thresholds, approval chains, evidence requirements, duplicate windows, signed records. Encoding all of that into every agent's system prompt is brittle and unauditable. Those controls belong in a runtime layer the agent calls, not inside the agent itself.

ActionRail is that layer. The first wedge is invoice approval and duplicate detection because they exercise the full transaction lifecycle on a vertical where mistakes are expensive and measurable.

## What the MVP proves

This MVP demonstrates the core primitive end-to-end:

1. An agent submits an invoice action via `POST /actions/preflight`.
2. ActionRail runs seven checks: `action_allowed`, `vendor_verified`, `duplicate_invoice`, `contract_match`, `amount_policy`, `evidence_attached`, `intent_lock`.
3. ActionRail returns a structured decision (`approval_required`, `blocked`, `needs_more_evidence`, or `allow`). The decision is deterministic, not probabilistic.
4. If approval is required, a human approves through the queue. Execution is a separate, gated step.
5. On execution, ActionRail produces an HMAC-SHA256 signed receipt over the canonical JSON payload — the decision, the evidence references, the approval, the execution timestamp.
6. A blocked transaction cannot be approved. A rejected transaction cannot execute. These are hard state guards, not soft suggestions.

The primitive is proved when the three demo flows all behave correctly. That is what this MVP is for.

## Current MVP scope

- Invoice approval **preflight** via `POST /actions/preflight`.
- **Vendor verification** against a seeded vendor registry.
- **Duplicate invoice detection** — same vendor + amount inside a configurable window.
- **Contract / evidence checks** — above-threshold invoices must reference an active contract whose vendor matches.
- **Amount policy checks** — approval threshold, critical threshold, senior-approval warnings.
- **Intent locks** — two agents cannot work the same invoice intent concurrently.
- **Approval / rejection** — state-gated. Blocked transactions cannot be approved; rejected transactions cannot execute.
- **Simulated execution** — execution boundary is explicit in the response and in the signed receipt.
- **HMAC-SHA256 signed receipt** over canonical JSON — tamper-evident, machine-verifiable.
- **Server-rendered dashboard** for human review, approvals, and demos (Jinja2 + static CSS, no JS framework).
- **Real local invoice upload** — upload a PDF, PNG, or JPG; extract text from digital PDFs; run OCR on images (if Tesseract is installed); show a **review screen** with pre-filled extracted fields so a controller can verify and correct values before ActionRail creates a transaction. This avoids creating finance transactions from untrusted OCR guesses.
- **Two-step upload flow**: upload → review → confirm → transaction. OCR can prefill fields; the user confirms or edits them before the preflight is run.
- **Basic field extraction** from digital PDF text using regex (invoice ID, amount, currency, dates, GST number). Image OCR via pytesseract (optional; not installed by default). See [`docs/OCR.md`](docs/OCR.md).
- **Demo reset script** (`scripts/reset_demo_db.py`) for clean recordings.
- **Local accounting sandbox writeback** — after simulated execution, create a draft bill JSON and audit packet JSON in the local sandbox. No ERP, bank, or ledger mutation is performed. This proves the accounting writeback boundary and prepares for real sandbox integrations in later phases.
- **`pytest` suite** covering the policy engine, dashboard routes, upload flow, accounting writeback, and the reset script.

## Current completion status

ActionRail Finance is MVP-complete as a local execution-control prototype with a **local control-plane foundation** (login, RBAC, CSRF, audit ledger on dashboard routes). It demonstrates invoice evidence intake, review, policy preflight, approval, simulated execution, signed receipts, and local accounting sandbox writeback. It is not production finance automation.

See [`docs/PROJECT_COMPLETION.md`](docs/PROJECT_COMPLETION.md) for the full completion checklist.

## What it does not do yet

These are deliberate deferments, not oversights.

- No real payments.
- No bank or payment-rail integration.
- No ERP or ledger writeback.
- No email / Gmail / Outlook ingestion.
- **Image OCR is optional, not installed by default.** Install `pytesseract` + the Tesseract binary for auto-extraction from image invoices. Without it, image uploads still work — enter fields manually on the review screen. See [`docs/OCR.md`](docs/OCR.md).
- **Digital PDF text extraction is basic** — regex-based, works for machine-generated PDFs. Scanned-to-image PDFs with no embedded text need OCR.
- **Amount extraction is intentionally conservative.** If amount confidence is low, the review screen asks for manual entry rather than creating a transaction with a guessed amount.
- Local demo security on the **JSON API** via API Keys (Phase 5D), but no production secret manager or API Gateway.
- No multi-tenant isolation.
- No external financial mutation of any kind.

The demo-execution boundary is codified in the code itself: `Demo execution only. No real bank or ledger mutation performed.` That string is part of every signed receipt's payload until a sandbox integration is explicitly built.

## Architecture

```text
AI finance agent
      ↓
ActionRail HTTP API  (FastAPI, Pydantic models)
      ↓
Preflight engine     (app/policy.py — checks, decision logic)
      ↓
Transaction store    (app/store.py — SQLite, seed data, query helpers)
      ↓
Decision returned to agent: allow | approval_required | blocked | needs_more_evidence
      ↓
Approval if required (separate HTTP call, separate state)
      ↓
Execution            (simulated; receipt signed on execution)
      ↓
HMAC-SHA256 receipt  (canonical JSON, tamper-evident)
```

- **FastAPI** — JSON API for agents + server-rendered HTML dashboard for humans.
- **SQLite** — six tables: `vendors`, `contracts`, `invoices`, `policies`, `intent_locks`, `transactions`.
- **Pydantic** — single source of truth for the agent-facing schema.
- **Jinja2** — dashboard templates, server-rendered, no client-side JavaScript.
- **Static CSS** — design tokens as CSS custom properties in `app/static/neo.css`.
- **`pytest`** — covers policy engine, dashboard routes, and the reset script.

## Project structure

```text
app/
  main.py        FastAPI routes (JSON API + dashboard + upload review)
  models.py      Pydantic request/response schemas
  policy.py      Preflight checks, decision logic, receipt signing
  store.py       SQLite schema, seed data, query helpers
  extraction.py  PDF text extraction + regex field extraction
  ocr.py         Optional OCR via pytesseract (graceful fallback)
  cli.py         Agent-facing CLI prototype
  templates/     Jinja2 templates (dashboard, transaction detail, receipt, upload, review)
  static/        neo.css — design tokens and utility classes
data/
  uploads/       Local uploaded invoice files (gitignored; .gitkeep committed)
  datasets/      Local OCR datasets (gitignored; .gitkeep committed)
examples/        Canonical demo payloads (approval-required, duplicate, missing-evidence)
scripts/         demo.sh, demo.ps1, reset_demo_db.py, check_ocr.py,
                 run_ocr_sample.py, inspect_invoice_dataset.py,
                 prepare_invoice_samples.py, evaluate_invoice_extraction.py,
                 download_sample_datasets.py
tests/           test_policy.py, test_dashboard.py, test_reset_demo_db.py,
                 test_upload.py, test_upload_review.py, test_ocr.py,
                 test_ocr_validation.py, test_extraction_safety.py,
                 test_datasets_script.py, test_ux_polish.py
docs/            PITCH.md, OCR.md, DATASETS.md, RELEASE_CHECKLIST.md, screenshots/
LICENSE          MIT License
PROJECT.md       Master product / architecture spec
TASKS.md         Working task log
DECISIONS.md     Architectural decisions with rationale
HANDOFF.md       Current state + how to run
CHANGELOG.md     Versioned change log
ForKnow.md       Append-only Cursor work journal
```

## Quickstart

### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
python scripts/reset_demo_db.py
uvicorn app.main:app --reload
```

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
python scripts/reset_demo_db.py
uvicorn app.main:app --reload
```

## URLs

```text
Dashboard:  http://127.0.0.1:8000/dashboard  (redirects to /login when signed out)
Login:      http://127.0.0.1:8000/login
Swagger:    http://127.0.0.1:8000/docs
Manifest:   http://127.0.0.1:8000/actionrail/manifest.json
Health:     http://127.0.0.1:8000/health
```

## Local demo authentication (dashboard only)

The dashboard control plane requires sign-in. **Local demo credentials only — not production authentication.**

```text
admin@example.local / admin123
controller@example.local / controller123
approver@example.local / approver123
executor@example.local / executor123
auditor@example.local / auditor123
viewer@example.local / viewer123
```

Roles: **viewer** (read dashboard/receipts) · **controller** (upload/review/demo preflight) · **approver** (approve/reject) · **executor** (execute + accounting writeback) · **auditor** (audit log) · **admin** (all).

Dashboard POST forms are CSRF-protected. Per-action audit events are written to the local SQLite audit ledger. The JSON API remains unchanged (JSON API routes are now protected by API Keys in Phase 5D).

**Admin control plane (Phase 5B):** sign in as `admin@example.local` and open `/dashboard/admin` to manage vendors, contracts, policy thresholds, and contract evidence uploads. All admin changes are audited. Still local prototype only — not production finance automation.

Production requires a real identity provider, RBAC policy administration, secure secret management (`ACTIONRAIL_SESSION_SECRET`), and audit-grade storage — not these demo passwords.

## Demo narrative

The three demo flows each prove a different part of the rail:

| Flow | What it proves |
|---|---|
| **Approval Required Invoice** — Acme Services, ₹83,000, contract attached, evidence attached | The approval gate works. A valid but above-threshold invoice is correctly held for human sign-off. The full `preflight → approved → executed → signed receipt` lifecycle completes. |
| **Duplicate Invoice** — same vendor + amount as a previously-paid invoice | The duplicate check works. ActionRail blocks the action before any damage is possible. The agent receives `decision=blocked` with the conflicting invoice as evidence. No execute button appears. |
| **Missing Evidence Invoice** — AWS, ₹12,000, no `evidence_urls` | The evidence gate works. ActionRail returns `needs_more_evidence`. Execution is blocked until evidence is attached. |

Together these three flows exercise all seven checks, all four decisions, and the full execution + receipt path.

## Real invoice upload demo

Upload a real invoice image or PDF and run the full ActionRail lifecycle from the browser.

### Prerequisites (image invoices)

```powershell
pip install pytesseract pillow
# Install Tesseract binary: https://github.com/UB-Mannheim/tesseract/wiki
$env:Path += ";C:\Program Files\Tesseract-OCR"   # Windows session fix
python scripts/check_ocr.py                       # Confirm OCR is ready
```

Digital PDFs work without OCR. Image uploads still work without OCR — you enter fields manually on the review screen.

### Sample images

```powershell
python scripts/prepare_invoice_samples.py --limit 10
# Files copied to data/datasets/kaggle-invoices-sample/
```

### Upload flow

1. Open <http://127.0.0.1:8000/dashboard/invoices/upload>
2. Upload `data/datasets/kaggle-invoices-sample/batch1-0001.jpg`
3. ActionRail runs OCR, extracts fields, and redirects to the **review screen**.
4. Review the extracted fields. If "Manual review required" appears (amount not extracted), enter the invoice amount.
5. Click **Create ActionRail transaction**.
6. From the transaction detail: **Approve** → **Execute** → **View Receipt**.
7. Return to transaction → **Create Accounting Sandbox Draft Bill** → view writeback page (draft bill JSON + audit packet JSON).

OCR can prefill fields, but you confirm every value before ActionRail creates a transaction. This avoids creating finance transactions from untrusted OCR guesses.

### Full real-upload + writeback flow

```txt
upload invoice → review fields → create transaction → approve → execute → view receipt
→ return to transaction → create accounting sandbox draft bill → view writeback page
```

---

## Browser demo flow

1. **Reset**: `python scripts/reset_demo_db.py`
2. **Start**: `uvicorn app.main:app --reload`
3. **Open** the dashboard: <http://127.0.0.1:8000/dashboard> — sign in as `controller@example.local` / `controller123` if prompted.
4. Click **Approval Required Invoice** → review the detail page (checks, evidence, decision, risk).
5. Click **Approve** → status becomes `approved`.
6. Click **Execute** → status becomes `executed`.
7. Click **View Receipt** → signed HMAC-SHA256 receipt with canonical payload.
8. Click **Create Accounting Sandbox Draft Bill** → writeback page with safety banner, draft bill JSON, audit packet JSON.
9. Return to the transaction — **View Accounting Sandbox Writeback** replaces the create button (no duplicate writebacks).
10. Return to dashboard → click **Duplicate Invoice** → `BLOCKED`, no Execute button.
11. Return to dashboard → click **Missing Evidence Invoice** → `NEEDS MORE EVIDENCE`, no Execute button.

After execution, the transaction page offers accounting sandbox writeback. Once created, the transaction page links to the existing writeback instead of creating duplicates.

## API demo flow

These are the same calls an AI finance agent would make. On Windows PowerShell use `curl.exe`.

### Preflight and capture transaction ID

```bash
TXN=$(curl -s -X POST http://127.0.0.1:8000/actions/preflight \
  -H "Content-Type: application/json" \
  -d @examples/invoice_approval_required.json | jq -r .transaction_id)
echo "$TXN"
```

### Approve

```bash
curl -X POST "http://127.0.0.1:8000/approvals/$TXN/approve" \
  -H "Content-Type: application/json" \
  -d '{"approver_id":"controller_001","note":"Looks valid"}'
```

### Execute

```bash
curl -X POST "http://127.0.0.1:8000/actions/$TXN/execute"
```

### Get the signed receipt

```bash
curl "http://127.0.0.1:8000/receipts/$TXN"
```

### Duplicate-blocked

```bash
curl -X POST http://127.0.0.1:8000/actions/preflight \
  -H "Content-Type: application/json" \
  -d @examples/invoice_duplicate_blocked.json
# decision=blocked, duplicate_invoice check failed
```

### Missing evidence

```bash
curl -X POST http://127.0.0.1:8000/actions/preflight \
  -H "Content-Type: application/json" \
  -d @examples/invoice_missing_evidence.json
# decision=needs_more_evidence
```

## Safety boundary

**Execution is simulated. No real money moves.**

This is a deliberate, codified design decision (see `DECISIONS.md` D3). The MVP proves the transaction rail — preflight, decision, approval, execution boundary, signed receipt. It is not a payment processor. Real bank, ERP, and payment-rail integrations are deferred to later phases and require production auth, secret management, RBAC, signed webhooks, and sandbox connectors.

Every execution response includes: `Demo execution only. No real bank or ledger mutation performed.` That line is part of the signed receipt payload.

## Screenshots

Screenshots not yet committed. Capture flow and naming convention: [`docs/screenshots/README.md`](docs/screenshots/README.md).

## Further reading

- [`PROJECT.md`](PROJECT.md) — master product / architecture spec.
- [`docs/PITCH.md`](docs/PITCH.md) — concise YC-style pitch.
- [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) — 2–3 minute demo walkthrough.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system design for reviewers.
- [`docs/SAFETY_BOUNDARY.md`](docs/SAFETY_BOUNDARY.md) — what is and is not real.
- [`docs/PROJECT_COMPLETION.md`](docs/PROJECT_COMPLETION.md) — MVP completion status.
- [`DECISIONS.md`](DECISIONS.md) — architectural decisions with rationale.
- [`HANDOFF.md`](HANDOFF.md) — current state + how to run.
- [`CHANGELOG.md`](CHANGELOG.md) — versioned change log.
- [`docs/RELEASE_CHECKLIST.md`](docs/RELEASE_CHECKLIST.md) — checklist before pushing a public release.

## License

MIT License. See [`LICENSE`](LICENSE).

Copyright (c) 2026 ActionRail Finance contributors.

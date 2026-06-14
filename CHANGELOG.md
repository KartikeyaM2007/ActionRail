# CHANGELOG

All notable changes to ActionRail Finance. Newest entries on top. Update on every change.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## 2026-06-14 — Agent Integration Examples (Phase 6E)

### Added
- `docs/AGENT_INTEGRATION.md` detailing the agent-first mental model, API endpoints, human-in-the-loop gating, and idempotency keys.
- `examples/agent_client.py` - Standard library Python client implementing HTTP request logic, idempotency headers, and structured decision branch handling.
- `examples/langgraph_actionrail_tool.py` - Blueprint showing integration with LangGraph framework workflows.
- `examples/openapi_tool_schema.json` - Tool/function calling definition schema for LLMs.
- `examples/README.md` - Quickstart details for running agent examples locally.
- `tests/test_agent_examples.py` - Validation suite for verifying examples importability and schema validity.

### Changed
- Lightly updated `README.md` with links to the new agent integration assets.
- Added agent-facing integration layer documentation and diagram to `docs/ARCHITECTURE.md`.

### Tests
- Full pytest suite passing with new tests added (256 passed).

---

## 2026-06-14 — Public GitHub/demo asset polish (Phase 6C)

### Added
- `docs/DEMO_VIDEO_SCRIPT.md` with full demonstration script.
- `docs/GITHUB_PUBLISHING.md` containing final checklist and repo metadata.
- `SECURITY.md` detailing the explicit local prototype boundary.

### Changed
- Finalized canonical screenshot list in `docs/screenshots/README.md`.
- Appended Phase 6C tasks to `docs/RELEASE_CHECKLIST.md`.
- Added demo asset links to `README.md`.

---

## 2026-06-14 — Release hardening, route consistency, security review, and final product closure (Phase 6A)

### Added
- Risk Monitor dashboard route (`/dashboard/risk`) protected by auditor/admin role.
- Security event capture in Risk Monitor (login failures, API auth failures, idempotency conflicts, approval separation denials).
- Strict data isolation tests for compliance.

### Changed
- Evidence packs now correctly generate as real ZIP files (`application/zip`) instead of dummy text.
- Evidence pack endpoint moved to `GET` for safe browser downloading.
- Updated `ROUTE_MAP.md`, `SCHEMA_MAP.md`, and `README.md` to reflect Phase 6A completion and correct routes.

### Fixed
- Fixed dashboard auth scopes so `view_evidence_pack`, `export_evidence_pack`, `view_transaction_replay`, and `view_risk_monitor` are strictly limited to `auditor` and `admin` roles, removing access for standard viewers.



## 2026-06-14 — Compliance evidence packs, replay, and risk monitoring (Phase 5E)

### Added
- Downloadable evidence packs (ZIP) containing transaction JSON, signed receipt, audit ledger trail, active policies, and vendor context.
- Historical policy replay to identify why an old transaction's decision would differ from the current policy.
- Transaction risk monitor panel showing real-time vendor risk, missing evidence flags, and duplicate invoice warnings.

### Changed
- Refactored test harness `_reset_db` to strictly clear the in-memory database between tests, preventing state bleeding across the test suite.

### Tests
```bash
pytest -q
```
```text
........................................................................ [ 28%]
........................................................................ [ 57%]
........................................................................ [ 85%]
....................................                                     [100%]
252 passed in 191.24s (0:03:11)
```

---

## 2026-06-14 — API Security and Idempotency (Phase 5D)

### Added
- Local API Key hashing (PBKDF2 HMAC-SHA256).
- Idempotency via `Idempotency-Key` headers on POST requests.
- Rate limiting per API client per minute using SQLite event counting.
- Scoped access logic (`preflight:create`, `transactions:read`, etc.).
- Admin UI for managing API clients.

### Changed
- Main API endpoints secured with dependency injection without modifying original response JSON schemas.

### Tests
```bash
pytest -q
.............................................................................................................................................................................................................................
221 passed in 100.25s
```

---

## 2026-06-14 — Context-retention and Antigravity handoff pass

### Added
- `docs/ANTIGRAVITY_HANDOFF.md`: Context-retention document for future AI coding agents.
- `docs/ROUTE_MAP.md`: Map of all current API and dashboard routes.
- `docs/SCHEMA_MAP.md`: Map of all current SQLite database tables.
- `docs/NEXT_PHASE_5C_PROMPT.md`: Clean future prompt saved for Phase 5C (Approval Workflow Engine).

### Tests
```bash
pytest -q
```
```text
196 passed in 87.26s
```

---

## 2026-06-14 — Policy admin, vendor onboarding, contract evidence (Phase 5B)

Local admin UI for vendors, contracts, policy thresholds, contract evidence. **196 tests pass.**

### Added

- **`app/admin_routes.py`**, admin templates, `contract_evidence` table/storage.
- **`tests/test_admin.py`** (21 tests).

### Changed

- **`app/store.py`**, **`app/policy.py`**, **`app/auth.py`**, **`app/control.py`**, docs.

### Tests

```bash
pytest -q
```

```text
196 passed in 87.26s
```

---

## 2026-06-14 — Authenticated control plane: local auth, RBAC, CSRF, audit ledger (Phase 5A)

Local dashboard control-plane foundation. JSON API response shapes unchanged. Receipt signature payload unchanged. **175 tests pass.**

### Added

- **`app/auth.py`** — PBKDF2 password hashing, six demo roles, permission map, CSRF helpers (stdlib only).
- **`app/control.py`** — session user resolution, login/logout, RBAC guards, audit writing, forbidden rendering.
- **`users` and `audit_events` SQLite tables** + store helpers in `app/store.py`.
- **Routes:** `GET/POST /login`, `POST /logout`, `GET /dashboard/audit`.
- **Templates:** `login.html`, `forbidden.html`, `audit_log.html`, `partials/control_nav.html`.
- **CSRF** hidden inputs on all dashboard POST forms.
- **Audit events** for login, logout, authorization_denied, csrf_failed, demo preflight, upload, review submit, approve/reject/execute, receipt view, writeback create/view.
- **Transaction-level audit trail** on transaction detail page.
- **`tests/test_auth.py`** — 20 auth/RBAC/CSRF/audit tests.
- **`tests/dash_helpers.py`** — shared login/CSRF helpers for dashboard tests.

### Changed

- **`app/main.py`** — SessionMiddleware, protected dashboard routes, RBAC enforcement, audit logging; approvals use logged-in user email.
- **Dashboard templates** — control nav, CSRF tokens, role-gated action buttons.
- **`scripts/reset_demo_db.py`** — drops/resets `users` and `audit_events`.
- **Existing dashboard tests** updated for login + CSRF.
- **Docs:** README, ARCHITECTURE, SAFETY_BOUNDARY, DEMO_SCRIPT, PROJECT_COMPLETION, RELEASE_CHECKLIST, TASKS, HANDOFF.

### Tests

```bash
pytest -q
```

```text
175 passed in 88.20s
```

---

## 2026-06-14 — Final MVP completion and public release polish (Phase 4A)

Documentation and dashboard wording polish for GitHub-ready MVP presentation. No product logic changes. **155 tests pass.**

### Added

- **`docs/DEMO_SCRIPT.md`** — 2–3 minute demo walkthrough (four flows + safety boundary + closing pitch).
- **`docs/ARCHITECTURE.md`** — high-level architecture, lifecycle, data model, policy, upload/OCR, receipt, writeback, local-only vs production.
- **`docs/SAFETY_BOUNDARY.md`** — what ActionRail does/does not do, simulated execution rationale, production requirements.
- **`docs/PROJECT_COMPLETION.md`** — honest MVP completion checklist (154+ tests, known limitations, roadmap).
- **`tests/test_dashboard.py`**: `test_dashboard_table_uses_preflight_decision_column`.

### Changed

- **`app/templates/dashboard.html`**: queue table column **Decision** → **Preflight Decision**.
- **`README.md`**: "Current completion status" section; links to new docs in Further reading.
- **`docs/RELEASE_CHECKLIST.md`**: git hygiene PowerShell commands; section 12 GitHub repo polish checklist with suggested topics.
- **`docs/screenshots/README.md`**: canonical 01–13 list at top; note that screenshots are optional for tests.

### Tests

```bash
pytest -q
```

```text
........................................................................ [ 46%]
........................................................................ [ 92%]
...........                                                              [100%]
155 passed in 7.03s
```

### What was not changed

- Policy logic, API JSON shapes, receipt signing, accounting writeback, stored transactions.

---

## 2026-06-14 — Dashboard stat correctness polish (Phase 3D)

Dashboard stat cards now count **current operational queue state**, not historical decision alone. An executed transaction with `decision=approval_required` counts only under Executed, not Approval Required. **154 tests pass.**

### Added

- **`app/main.py`**: `_compute_dashboard_stats(counts)` — readable stat aggregation for dashboard UI only.
- **`tests/test_dashboard.py`**: 8 Phase 3D tests — unit tests for stat helper; integration tests parsing dashboard HTML after demo flows.

### Changed

- **`app/main.py`**: `dashboard()` route uses `_compute_dashboard_stats()` instead of inline decision-only counting.

Stat rules:

- **Total**: all transactions
- **Approval required**: `decision == "approval_required"` AND `status == "preflighted"`
- **Needs evidence**: `decision == "needs_more_evidence"` AND status not in `{executed, approved, rejected}`
- **Blocked**: `status == "blocked"` OR `decision == "blocked"`
- **Executed**: `status == "executed"`

### Tests

```bash
pytest -q
```

```text
........................................................................ [ 46%]
........................................................................ [ 93%]
..........                                                               [100%]
154 passed in 7.44s
```

### What was not changed

- Stored transaction records, policy logic, API JSON shapes, receipt semantics, accounting writeback, dashboard table rows.

---

## 2026-06-14 — Final transaction state polish and screenshot readiness (Phase 3C)

Fixed stale `request_finance_approval` showing in the transaction detail overview after execution. Added UI-only `display_next_action` and compact state summary banner. **146 tests pass.**

### Added

- **`app/main.py`**: `_display_next_ui_action()` — derives correct next action from status/decision/writeback state without mutating stored records; `_transaction_state_summary()` — compact banner text for executed/blocked/approval-required states.
- **`tests/test_accounting.py`**: 5 Phase 3C tests — next action for approval-required, blocked, approved, executed±writeback; state summary copy; Create→View button transition.

### Changed

- **`app/templates/transaction_detail.html`**: overview label changed to "Next UI action" using `display_next_action`; state summary banner via `neo-review-warning` when applicable.
- **`app/main.py`**: `_render_detail()` passes `display_next_action` and `state_summary` to template.
- **`README.md`**: one line on writeback linking after creation; browser demo step 9 for View button.
- **`docs/screenshots/README.md`**: added `13-executed-transaction-with-writeback.png`; expanded capture notes for pre/post writeback detail and expanded JSON panels.

### Tests

```bash
pytest -q
```

```text
........................................................................ [ 49%]
........................................................................ [ 98%]
..                                                                       [100%]
146 passed in 8.72s
```

### Known limitations

- Raw transaction JSON at page bottom still shows stored `allowed_next_action` from preflight — intentional; only the overview "Next UI action" field is UI-corrected.

---

## 2026-06-14 — Accounting writeback validation, UX polish, demo hardening (Phase 3B)

Polished the accounting sandbox writeback flow for demo and screenshot readiness. Writeback page now uses clearer safety copy and `local://` references instead of file paths. Transaction detail shows Create vs View writeback buttons conditionally. Receipt payload unchanged. **141 tests pass.**

### Added

- **`tests/test_accounting.py`**: 5 new tests — create button after execution, view button after writeback, idempotent POST redirect, no absolute paths on writeback page, draft bill receipt signature and audit packet checks/receipt on page.

### Changed

- **`app/templates/accounting_writeback.html`**: updated safety banner and subtitle copy; summary shows transaction ID, provider, status, draft bill ID, created at, `local://` draft bill and audit packet references, safety note; removed raw file path fields; collapsible JSON blocks retained.
- **`app/templates/transaction_detail.html`**: Create Accounting Sandbox Draft Bill only when executed and no writeback; View Accounting Sandbox Writeback when writeback exists; new accounting sandbox section with boundary copy.
- **`app/main.py`**: `_has_accounting_writeback()` helper; `has_accounting_writeback` in detail context; writeback GET loads JSON via `LocalAccountingSandboxAdapter` dirs; passes `draft_bill_ref` / `audit_packet_ref` as `local://accounting_sandbox/...`; `_ACCOUNTING_PROVIDER` moved to module-level constants.
- **`README.md`**: browser demo flow includes writeback step; real-upload section documents full writeback sequence.
- **`docs/RELEASE_CHECKLIST.md`**: writeback smoke steps expanded; optional screenshot 12 noted.
- **`docs/screenshots/README.md`**: added `12-accounting-sandbox-writeback.png` and recommended full demo sequence including writeback.

### Tests

```bash
pytest -q
```

```text
........................................................................ [ 51%]
.....................................................................    [100%]
141 passed in 7.52s
```

### Known limitations

- Writeback still uses local sandbox JSON files only — no real ERP integration.
- Signed receipt payload does not include writeback metadata (intentional — preserves receipt semantics).

---

## 2026-06-14 — Accounting sandbox writeback foundation (Phase 3A)

After simulated execution, ActionRail can now create a local accounting sandbox draft bill and audit packet. No ERP, bank, or ledger mutation is performed — this is a safe local adapter that proves the accounting writeback boundary. **136 tests pass.**

### Added

- **`app/accounting.py`** — new module:
  - `AccountingDraftBill` Pydantic model: invoice fields, receipt ID, receipt signature, provider, sandbox note.
  - `AccountingAuditPacket` Pydantic model: full transaction, receipt, checks, approval, execution, evidence reference, writeback metadata.
  - `AccountingWritebackResult` Pydantic model: writeback ID, provider, status, external_id, relative file paths, sandbox note.
  - `LocalAccountingSandboxAdapter.create_draft_bill(transaction)`: validates `status=executed` and receipt exists, writes draft bill JSON and audit packet JSON to `data/accounting_sandbox/`, returns result with relative paths.
  - `SANDBOX_SAFETY_NOTE` constant: `"Local sandbox only. No ERP, bank, or ledger mutation performed."`
- **`app/templates/accounting_writeback.html`** — new Jinja2 template: sandbox writeback page with yellow safety banner, writeback summary DL, collapsible draft bill JSON, collapsible audit packet JSON, links back to transaction and dashboard.
- **`data/accounting_sandbox/draft_bills/.gitkeep`** — directory tracked in git; draft bill files gitignored.
- **`data/accounting_sandbox/audit_packets/.gitkeep`** — directory tracked in git; audit packet files gitignored.
- **`tests/test_accounting.py`** — 13 tests: adapter rejects non-executed, creates draft bill, creates audit packet, receipt signature in result, idempotency, DB store/retrieve, no writeback button before execution, writeback button after execution, POST creates and redirects, GET shows safety note, upload flow unaffected, demo flow unaffected, API shapes unchanged.

### Changed

- **`app/store.py`**: `init_db()` now creates `accounting_writebacks` table with `UNIQUE(transaction_id, provider)` constraint. Added `save_accounting_writeback()` (idempotent via `INSERT ... ON CONFLICT DO UPDATE`), `get_accounting_writeback()`, `list_accounting_writebacks()`.
- **`app/main.py`**: imported `get_accounting_writeback` and `save_accounting_writeback`. Added `POST /dashboard/transactions/{id}/writeback/accounting-sandbox` (create writeback or redirect if exists) and `GET /dashboard/transactions/{id}/writeback/accounting-sandbox` (show writeback page loading draft bill + audit packet files). Added `_ACCOUNTING_PROVIDER = "local_accounting_sandbox"` constant.
- **`app/templates/transaction_detail.html`**: added "Create accounting sandbox draft bill" form button and "View accounting sandbox writeback" link when `txn.status == 'executed'`.
- **`scripts/reset_demo_db.py`**: `accounting_writebacks` added as first entry in `PROJECT_TABLES` (dropped before the others).
- **`.gitignore`**: added patterns for `data/accounting_sandbox/draft_bills/*` and `data/accounting_sandbox/audit_packets/*` with `.gitkeep` exceptions.
- **`README.md`**: MVP scope updated to mention local accounting sandbox writeback.
- **`docs/PITCH.md`**: "What the current MVP proves" gains point 7 about accounting sandbox writeback.
- **`docs/RELEASE_CHECKLIST.md`**: writeback step added to the core demo flow checklist.

### Tests

```bash
pytest -q
```

```text
........................................................................ [ 52%]
................................................................         [100%]
136 passed in 8.85s
```

### Safety boundary

Every writeback carries: `"Local sandbox only. No ERP, bank, or ledger mutation performed."`

The `LocalAccountingSandboxAdapter` never makes network calls. It writes only to `data/accounting_sandbox/` which is gitignored.

---

## 2026-06-14 — Final demo packaging and public repo hygiene (Phase 2F)

Documentation-only pass for GitHub/YC/demo release readiness. **No production code changed. All 123 tests still pass.**

### Added

- **`LICENSE`** — MIT License, `Copyright (c) 2026 ActionRail Finance contributors`.
- **`docs/RELEASE_CHECKLIST.md`** — 11-step pre-release checklist: `pytest -q`, DB reset, OCR check, sample validation, dashboard smoke, core demo flow, real-upload flow, git hygiene checks (no `.db`, no datasets, no uploads, no `kaggle.json` staged), README/docs review, screenshots, push.

### Changed

- **`README.md`**:
  - Project structure tree updated to accurately reflect all files added since Phase 1 (`app/extraction.py`, `app/ocr.py`, `data/`, all 10 test files, all scripts, all docs).
  - License section changed from "Internal/demo project. Add a license file." to "MIT License. See LICENSE."
  - "Further reading" now links to `docs/RELEASE_CHECKLIST.md`.
- **`docs/PITCH.md`**: "What the current MVP proves" section gains point 6 — real local invoice upload with OCR-assisted extraction and review-before-transaction. Explicit note that execution is simulated.
- **`docs/screenshots/README.md`**: recommended clean-state section adds browser zoom guidance (90–100%) and a note to prepare Kaggle sample images plus a warning against committing real invoice images.
- **`HANDOFF.md`**: "Important files" table extended with `LICENSE` and `docs/RELEASE_CHECKLIST.md`; "What to do next" updated to reflect licenses done, screenshots and GitHub push as the remaining tasks.

### Tests

```bash
pytest -q
```

```text
........................................................................ [ 58%]
...................................................                      [100%]
123 passed in 8.52s
```

---

## 2026-06-14 — Real-upload demo UX polish (Phase 2E)

Template and CSS polish for the real-invoice-upload browser experience. No app logic changed. **123 tests pass.**

### Changed

- **`app/templates/invoice_review.html`**:
  - Header subtitle explicitly states "OCR is only a suggestion" and "you must review and confirm".
  - Yellow "Manual review required" banner (`.neo-review-warning`) shown prominently when `doc.manual_review_required` is true; text: "Amount was not confidently extracted. Enter or confirm the amount before creating a transaction."
  - Document summary replaced with a compact `<dl class="neo-doc-summary">` showing filename, doc ID, file size, SHA-256 short (16 chars + `…`), and extraction status + OCR engine/status.
  - Extraction notes use the new `.neo-note-list` with per-item classes: `.neo-note--ocr` (violet) for OCR-related notes, `.neo-note--manual` (yellow) for "manual review" or "not confidently" notes.
  - Amount field: when extracted, shows "(extracted, verify before confirming)" label in muted gray; when missing, shows "(enter manually)" in red; missing amount auto-focuses the field.
  - Extracted text moved into a `<details class="neo-details">` accordion (collapsed by default, title "Show extracted text").
- **`app/templates/invoice_upload.html`**: subtitle now says "Upload a real invoice PDF or image" and "You confirm every field before anything is created."
- **`app/templates/transaction_detail.html`** (uploaded evidence section):
  - Renamed section from "Uploaded document" to "Uploaded evidence".
  - SHA-256 now shows short display (first 16 chars + `…`; full value in `title` attribute).
  - Extraction status + OCR engine/status shown inline.
  - Evidence reference shown explicitly as `local://uploaded_documents/{id}`.
  - New "Reviewed before transaction" row with `.neo-reviewed-stamp` ("Yes — fields confirmed by user").
  - Extraction notes use `.neo-note-list` with variant classes.
  - Extracted text in a `<details class="neo-details">` accordion.
- **`app/static/neo.css`** — new classes (section 16):
  - `.neo-review-warning` (+ `__title`, `__body`) — yellow warning box with thick left accent.
  - `.neo-note-list` (+ `li`, `li.neo-note--ocr`, `li.neo-note--manual`) — styled extraction notes list.
  - `.neo-doc-summary` (`dt`, `dd`, `dd.neo-doc-summary__plain`) — compact definition-list grid.
  - `details.neo-details` (+ `summary`, `[open] summary::after`, `.neo-details__body`) — CSS-only accordion.
  - `.neo-reviewed-stamp` — black uppercase stamp for the "reviewed before transaction" indicator.
- **`README.md`**: new "Real invoice upload demo" section with prerequisites, sample image preparation, and 6-step upload flow.
- **`docs/OCR.md`**: added "upload browser demo" as step 4 in the manual testing section.
- **`docs/screenshots/README.md`**: added 4 new screenshot entries (08–11) for the real-upload demo flow.

### Added

- **`tests/test_ux_polish.py`** — 9 tests: upload page review copy, review page safety copy, manual review warning when amount missing, editable pre-filled fields, collapsible extracted text, transaction detail uploaded evidence and stamp, two-step flow regression, demo flow regression, API shapes.

### Tests

```bash
pytest -q
```

```text
........................................................................ [ 58%]
...................................................                      [100%]
123 passed in 5.52s
```

---

## 2026-06-14 — Invoice upload review screen (Phase 2D)

Invoice upload is now a two-step flow: upload file → review extracted fields → confirm and create transaction. This prevents creating finance transactions from unverified OCR guesses. **114 tests pass.**

### Added

- **`GET /dashboard/invoices/review/{doc_id}`** — review screen. Shows document summary (filename, file size, SHA-256), extraction quality indicator, extraction notes, all editable invoice fields pre-filled from OCR/extraction, explicit warning when amount is missing ("not confidently extracted"), and a submit button.
- **`POST /dashboard/invoices/review/{doc_id}/submit`** — reads confirmed form fields; validates required fields (invoice_id, vendor, amount); builds PreflightRequest; redirects to transaction detail on success; re-renders review page with error on failure.
- **`app/templates/invoice_review.html`** — new Jinja2 template using existing neo-brutalist CSS classes.
- **`tests/test_upload_review.py`** — 10 tests covering the new two-step flow.

### Changed

- **`POST /dashboard/invoices/upload`** now only accepts `file`. It stores the document and runs extraction, then redirects to `/dashboard/invoices/review/{doc_id}`. **It no longer creates a transaction.** This is the key safety change.
- **`app/templates/invoice_upload.html`** simplified to a file-only upload form. Manual fields moved to the review screen.
- **`app/store.py`**:
  - `save_uploaded_document()` gains two new keyword args: `extraction_status` and `ocr_metadata`. Both are stored under a `_meta` key inside `extracted_fields_json` — no schema migration needed.
  - `get_uploaded_document()` now returns clean top-level keys: `extraction_status`, `ocr_metadata`, `manual_review_required` (derived from whether `amount` was extracted).
- **`tests/test_upload.py`** fully rewritten to use the two-step flow. The upload → review → submit sequence is tested end-to-end.
- **`tests/test_ocr.py`**, **`tests/test_extraction_safety.py`** — tests that previously posted manual fields directly to the upload route updated to use the two-step flow.
- **`README.md`** — "What it does" section updated to describe the review-before-transaction flow and the conservative amount extraction.

### Tests

```bash
pytest -q
```

```text
........................................................................ [ 63%]
..........................................                               [100%]
114 passed in 8.92s
```

---

## 2026-06-14 — Safer extraction and OCR confidence gating (Phase 2C)

Extraction is now safer: no false currency from US addresses, no amounts from item quantities, and field-specific error messages when a field can't be extracted. **94 tests pass.**

### Changed

- **`app/extraction.py`** — safer extraction:
  - `_detect_currency()`: replaced keyword-substring scan with explicit regex patterns that require word-boundary or symbol evidence. `INR` now requires `₹`, `\bINR\b`, `\bRs\.?\b`, or `\bRupees?\b`; `USD` requires `\$`, `\bUSD\b`, or `\bUS\s+DOLLARS?\b`. Bare `IN` (Indiana state abbreviation) no longer triggers INR.
  - `_extract_amount_with_confidence()`: new confidence-gated function. Searches lines for high-confidence labels (amount due, balance due, grand total, invoice total, total amount, amount payable, net payable — priority 1; subtotal — priority 2; total — priority 3). Also accepts explicit currency-prefixed numbers (`$`, `₹`, `INR`, `USD`) as priority 2 without a label. Bare-number fallback completely removed. Values < 10 rejected. `total`-only lines require a currency symbol. Returns `(amount | None, notes)`.
  - `_AMOUNT_REJECT_LABEL_PATTERN`: rejects amounts from lines starting with `Qty`, `Quantity`, `No.`, `Tax Id`, `IBAN`, `Date`, `Invoice no` — prevents picking up row numbers and item quantities.
  - `extract_fields_from_text()` return shape unchanged; notes now clearly say "Manual review required: amount not confidently extracted." when amount is skipped.
  - `_parse_amount()`: rejects negative and zero values.

- **`app/main.py`** upload route:
  - Fixed `UnboundLocalError`: OCR-extracted fields now merged into `extraction_result["fields"]` before the `extracted_fields = extraction_result.get("fields", {})` assignment.
  - Improved 400 error messages: amount-specific message is "Amount could not be confidently extracted. Please enter the invoice amount manually." Other fields show their own specific message.

- **`scripts/run_ocr_sample.py`**: summary block now prints `amount_extracted`, `amount_missing`, `currency_extracted`, `manual_review_required` counts.

- **`tests/test_ocr_validation.py`**: two tests updated to use multi-line text that matches real OCR format (single-line text like `"Invoice no: INV-001 $1,234.56"` fails the `_AMOUNT_REJECT_LABEL_PATTERN` check; multi-line text works correctly).

- **`tests/test_upload.py`**: `test_upload_missing_required_fields_returns_400` assertion updated to match the new field-specific error messages.

### Added

- **`scripts/evaluate_invoice_extraction.py`**: reads OCR text from Kaggle invoice CSV annotations and reports extraction coverage without requiring images or Tesseract. Fields covered: `invoice_id`, `vendor`, `invoice_date`, `amount`, `currency`. Prints 3 examples where amount was skipped. `--limit N` and `--csv-path` flags.
- **`tests/test_extraction_safety.py`**: 24 offline tests covering currency false-positive prevention (US state abbreviations, address text), amount confidence gating (no extraction from quantities/tax-IDs/bare lines), labelled total extraction (Amount Due, Grand Total, INR prefix, ₹ symbol), upload route manual override wins, 400 error message specificity, regressions (INR/GST, PDF upload, API shapes).

### OCR smoke test results (Phase 2C, Tesseract 5.4.0)

- 5/5 OCR ok
- Currency false-positive eliminated: `Lake Daniellefurt, IN 57228` → no INR
- Amount extracted on 4/5 (one invoice had no `$` signs in the OCR text preview)
- Extracted amounts: 623, 44, 819, 797 (much more plausible than previous 4.0–5.0 from bare fallback)
- 1/5 amount correctly skipped with "Manual review required" note

### Evaluator coverage (50 rows from batch1_1.csv)

- invoice_id: 100%
- invoice_date: 100%
- currency: 100% (USD from `$` signs on item lines)
- vendor: 0% (flat single-line OCR format; vendor inference needs multi-line structure)
- amount: 0% (Kaggle CSV OCRed Text doesn't include labelled total lines; amount requires manual entry for this dataset)

### Tests

```bash
pytest -q
```

```text
........................................................................ [ 76%]
......................                                                   [100%]
94 passed in 3.92s
```

---

## 2026-06-14 — OCR smoke test and extraction improvement (Phase 2B-validation)

Tesseract 5.4.0 validated on the Kaggle invoice samples (5/5 OCR ok), USD extraction improved in the regex extractor. **All 70 tests pass.**

### Added

- **`scripts/check_ocr.py`** — prints status of Pillow, pytesseract, Tesseract binary, version; Windows PATH session fix and permanent fix; never crashes on missing deps.
- **`scripts/run_ocr_sample.py`** — iterates image files in `data/datasets/kaggle-invoices-sample/`, runs `ocr_image_bytes()`, runs `extract_fields_from_text()`, prints per-image results. `--save-report` flag saves JSON to `data/datasets/ocr_reports/latest_ocr_report.json`.
- **`data/datasets/ocr_reports/.gitkeep`** — report directory tracked; report files gitignored.
- **`tests/test_ocr_validation.py`** — 14 offline tests: `check_ocr` exits cleanly with missing tesseract/pytesseract; `run_ocr_sample` handles missing/empty folder; `run_ocr_sample` with mocked OCR; USD `$` amount extraction; labelled `Amount Due: $X` extraction; `Invoice #` number extraction; `$` → USD currency inference; INR amount still works; GST still extracted; PDF upload unaffected; PNG upload without OCR still passes; API shapes unchanged.

### Changed

- **`app/extraction.py`** (conservative improvements):
  - USD amount patterns: `$1,234.56` (bare `$` sign), `Amount Due: $1,234.56`, `Balance Due`, `Grand Total`, `Invoice Total` labelled totals. Bare-number fallback now requires a proper thousands separator (`1,234` not `4,00`) to avoid triggering on European-format quantity values.
  - Invoice ID patterns: whitespace in capture group removed; IDs now captured until the first non-alphanumeric boundary, preventing multiline artefacts.
  - Date patterns: added `MM/DD/YYYY` and `DD/MM/YYYY` slash formats (common in the Kaggle dataset).
  - Vendor inference: added `_try_extract_vendor()` — takes first plausible non-generic line from the top of the OCR text. Returns `None` if nothing confident is found (no hallucination). Skips address lines, generic finance keywords, and very short tokens.
- **`docs/OCR.md`**: added Windows session PATH fix (`$env:Path += ...`), permanent PATH fix, added `check_ocr.py` and `run_ocr_sample.py` steps to the manual testing section.
- **`.gitignore`**: added `data/datasets/ocr_reports/*` and `!data/datasets/ocr_reports/.gitkeep`.

### OCR smoke test results (Tesseract 5.4.0.20240606)

- 5 images tested from `data/datasets/kaggle-invoices-sample/`
- 5/5 returned `status=ok`
- Invoice IDs extracted on all 5 (bare numeric IDs like `51109338`)
- Vendor names extracted on all 5 (multi-word company names correctly identified)
- Currency detected: 4 × USD, 1 × INR
- Dates extracted on 4/5 (date of issue MM/DD/YYYY format)
- Amounts: baseline numeric amount extracted; total-line amount still misses on these invoices because the OCR text does not contain a labelled total line that matches current patterns — known limitation (see below)

### Known limitations

- Amount extraction accuracy is limited on these Kaggle invoices. The dataset's OCR text does not reliably produce a labelled "Total:" line that the patterns can anchor on. The bare-number fallback picks up the first item's quantity (e.g. `4,00` = 4.0) rather than the invoice total. Users can override the amount manually in the upload form.
- `pytesseract` and `pillow` are still **not** in `requirements.txt` — they are optional dev/testing dependencies.

### Tests

```bash
pytest -q
```

```text
......................................................................   [100%]
70 passed in 3.27s
```

---

## 2026-06-14 — OCR and dataset sample tooling (Phase 2B)

Optional OCR for image invoices, dataset inspection tools, and sample preparation script. **OCR is never required for app startup. All 56 tests pass.**

### Added

- **`app/ocr.py`** — optional OCR module. `ocr_image_bytes(data, filename) -> dict`. Tries `pytesseract` + `Pillow` if installed; gracefully returns `status="not_available"` if either is missing or the Tesseract binary is not on PATH. Never raises on import. Returns `{status, engine, text, notes}` consistently. Notes include actionable install instructions when OCR is unavailable.
- **`scripts/inspect_invoice_dataset.py`** — prints the full local dataset structure: total files, image counts, extension breakdown, folder layout, first 10 image paths, CSV annotation details (columns, row count, JSON key sample, OCR text sample). Handles missing dataset path gracefully.
- **`scripts/prepare_invoice_samples.py`** — copies up to `--limit N` JPG/PNG/JPEG/TIFF images from `data/datasets/kaggle-invoices` to `data/datasets/kaggle-invoices-sample/`. Prints copied paths. Handles missing source gracefully. Default limit: 20.
- **`data/datasets/kaggle-invoices-sample/.gitkeep`** — directory tracked; contents gitignored.
- **`docs/OCR.md`** — optional OCR setup guide: Windows + Linux/macOS install steps, pytesseract verification, manual testing instructions, dataset context (CSV `OCRed Text` column), limitations table.
- **`tests/test_ocr.py`** — 11 offline tests: `ocr_image_bytes` returns `not_available` when pytesseract missing; returns `not_available` when Pillow missing; always returns the required response keys; upload PNG without OCR still redirects; upload stores OCR notes; PDF upload still works; existing demo flow unaffected; inspect script handles missing path; prepare-samples handles missing source; prepare-samples copies fake images; JSON API shapes unchanged.

### Changed

- **`app/main.py`** upload route: image (PNG/JPG/JPEG) path now calls `app.ocr.ocr_image_bytes(file_bytes)`. If `status="ok"` and text is returned, the text is passed to `extract_fields_from_text()`. OCR notes (`engine`, `status`, any warnings) are stored in the `uploaded_document.extraction_notes_json`. If OCR is unavailable, the existing manual-fields path applies unchanged.
- **`app/main.py`** upload route: removed the now-unused `extraction_status_for_image` import from `app.extraction`.
- **`.gitignore`**: added `data/datasets/kaggle-invoices-sample/*` and `!data/datasets/kaggle-invoices-sample/.gitkeep`.
- **`docs/DATASETS.md`**: added local dataset structure section (8,181 JPG images + 3 annotation CSVs with columns `File Name`, `Json Data`, `OCRed Text`; folder layout; `inspect` and `prepare` script links).
- **`README.md`**: "What it does not do yet" updated — image OCR is now optional (install pytesseract + Tesseract) rather than a hard limitation; link to `docs/OCR.md`.

### Dataset discovery (Phase 2B research)

The Kaggle invoice dataset contains:
- **8,181 JPG images** across 3 top-level batches.
- **3 CSV annotation files** each with columns: `File Name`, `Json Data` (structured invoice JSON with client/seller names, invoice number, dates, line items, subtotal), `OCRed Text` (pre-computed OCR text from each image).
- This means you can test ActionRail's regex field extractor against real invoice text **without running Tesseract locally** — use the `OCRed Text` column from the CSVs.

### Tests

```bash
pytest -q
```

```text
........................................................                 [100%]
56 passed in 2.34s
```

### Known limitations

- pytesseract is not in `requirements.txt`. Install separately: `pip install pytesseract pillow`.
- Tesseract binary must be installed separately (Windows: download from UB Mannheim; Linux: `apt-get install tesseract-ocr`).
- The regex extractor is tuned to USD/EUR amount patterns from the Kaggle dataset. INR-specific invoices may need the amount pattern extended.

---

## 2026-06-13 — Kaggle credential safety and dataset downloader (Phase 2A-fix2)

Kaggle credential protection, a working download script with `--check-kaggle` and `--download` modes, updated dataset docs, and 7 new offline tests. **No production code changed. No new Python dependencies.**

### Changed

- **`.gitignore`**: added `kaggle/`, `kaggle.json`, `**/kaggle.json`, `.kaggle/` — project-local credentials are now gitignored at every path.

- **`scripts/download_sample_datasets.py`** fully rewritten:
  - `KaggleCredStatus` named tuple for credential detection results.
  - `detect_kaggle_credentials()` — three-level priority: Windows official (`%USERPROFILE%\.kaggle\kaggle.json`) → Linux/macOS official (`~/.kaggle/kaggle.json`) → project-local fallback (`kaggle/kaggle.json`). Project-local fallback sets `KAGGLE_CONFIG_DIR` and prints a warning.
  - `kaggle_package_available()` — checks `importlib.util.find_spec("kaggle")` plus `shutil.which("kaggle")` fallback.
  - `configure_kaggle_env()` — sets `KAGGLE_CONFIG_DIR` when using project-local credentials.
  - `check_kaggle()` — `--check-kaggle` mode: prints package status, credential path (never contents), repo-containment warning if applicable, and platform-specific setup instructions if credentials are missing.
  - `print_kaggle_instructions()` — `--instructions` mode: prints the exact `kaggle datasets download` CLI command.
  - `download_kaggle_invoices(limit)` — `--download` mode: pre-flight checks (package + credentials), sets env, runs kaggle CLI via subprocess, handles non-zero exit with actionable error messages (403, 401, etc.), optionally extracts a sample subset.
  - `_extract_sample(base_dir, limit)` — copies up to `limit` image/PDF files into `base_dir/sample/`.
  - `kaggle-invoices` added as a named `--source` option.
  - All existing flags and `--source funsd --limit N` remain backward compatible.
  - `print_links()` updated to include Kaggle and FUNSD usage hints.

- **`docs/DATASETS.md`** fully rewritten:
  - Security section at top (never commit `kaggle.json`; gitignore paths listed).
  - "Kaggle setup on Windows" section with full `pip install kaggle`, `mkdir`, `copy`, `--check-kaggle`, `--download` command sequence.
  - "Kaggle setup on Linux/macOS" section with `chmod 600`.
  - "Common Kaggle errors" troubleshooting table (7 rows: 403, 401, missing creds, CLI not recognized, terms not accepted, not found, ModuleNotFoundError).
  - `kaggle-invoices` source key documented in the dataset entry.
  - "Quick reference" command table at the bottom.

### Added

- **`tests/test_datasets_script.py`** — 7 offline tests:
  1. `check_kaggle()` with no credentials prints setup instructions, exits cleanly.
  2. Project-local `kaggle/kaggle.json` detection with a temp fake credential file.
  3. `.gitignore` contains `kaggle/` or `kaggle.json` or `**/kaggle.json`.
  4. `print_kaggle_instructions()` outputs the correct dataset command.
  5. Unknown `--source` argument exits with code 1 or 2.
  6. `download_kaggle_invoices()` without kaggle package installed exits cleanly with a message.
  7. `download_kaggle_invoices()` without credentials exits cleanly with a message.

### Tests

```bash
pytest -q
```

```text
.............................................                            [100%]
45 passed in 1.96s
```

### Known limitations

- The `kaggle` Python package is not in `requirements.txt` — it is an optional dev dependency for dataset work only, not required for the ActionRail demo or tests. Install separately: `pip install kaggle`.
- The real Kaggle download is only ready once the `kaggle` package is installed (`pip install kaggle`). The credential at `%USERPROFILE%\.kaggle\kaggle.json` is already in place on this machine.

---

## 2026-06-13 — Real invoice upload and extraction (Phase 2A)

A user can now upload a real PDF, PNG, or JPG invoice from the dashboard, have basic fields extracted from digital PDFs, enter/override fields manually, and run the full ActionRail preflight → approval → execution → receipt lifecycle against the uploaded file. **Execution remains simulated. No real money moves.**

### Added

- **`data/uploads/`** — local evidence storage directory. Gitignored (only `.gitkeep` committed). Upload files are stored here with a safe generated filename derived from a `doc_` UUID.
- **`data/datasets/`** — local dataset storage for Phase 2B+ OCR testing. Gitignored. Only `.gitkeep` committed.
- **`app/extraction.py`** — two-layer extraction module:
  - `extract_text_from_pdf(path)` — uses pypdf to extract plain text from digital PDFs. Returns `(text, status)`. Status is `"ok"`, `"empty"`, `"not_a_pdf"`, or `"extraction_error:<msg>"`.
  - `extract_fields_from_text(text)` — conservative regex-based field extraction returning `{"fields": {...}, "notes": [...]}`. Extracts: invoice_id, amount, currency, invoice_date, due_date, gst_number. Misses are safe; nothing is hallucinated.
  - `extraction_status_for_image(content_type)` — extension point for Phase 2B OCR. Currently returns `"not_available_without_ocr"`.
- **`uploaded_documents` table** added to SQLite schema in `app/store.py`. Columns: id, original_filename, stored_filename, content_type, file_size, sha256, storage_path, extracted_text, extracted_fields_json, extraction_notes_json, created_at.
- **`save_uploaded_document()` + `get_uploaded_document()`** helpers in `app/store.py`.
- **`GET /dashboard/invoices/upload`** — serves the upload form (Jinja2 template, static CSS, neo-brutalist styling, safety disclaimer: "Execution remains simulated. No real money moves.").
- **`POST /dashboard/invoices/upload`** — async multipart handler: validates extension + content-type (PDF/PNG/JPG only), hashes file (SHA-256), stores to `data/uploads/`, runs extraction (PDF only), merges manual form fields over extracted fields, validates required fields (invoice_id, vendor, amount), saves uploaded_documents record, runs `run_preflight(conn, req)`, and 303-redirects to the transaction detail page.
- **"Upload real invoice"** link added to the dashboard header nav.
- **Uploaded document info block** on `transaction_detail.html` — rendered when the transaction's evidence URL starts with `local://uploaded_documents/`. Shows: document ID, original filename, file size, SHA-256, extracted fields JSON, extraction notes, first 400 chars of extracted text.
- **`docs/DATASETS.md`** — reference list of 6 publicly available invoice/receipt datasets (High Quality Invoice Images, FATURA, SROIE, CORD, FUNSD, RVL-CDIP) with dataset links, format descriptions, and license notes.
- **`scripts/download_sample_datasets.py`** — prints links and instructions by default; supports `--source funsd --limit N` to auto-download a FUNSD sample via the `datasets` library.
- **`app/main.py`**: `_UPLOAD_DIR` constant, `_doc_id()`, `_sha256_of_bytes()` helpers; upload routes; `_detail_view_model()` extended to resolve `uploaded_doc` from the evidence URL.
- **`tests/test_upload.py`** — 13 tests: upload page loads, invalid extension rejected, PNG with manual fields redirects, detail page accessible, PDF stores SHA-256 and evidence ref, missing required fields returns 400, field extraction from text, empty text handled, minimal PDF extraction, non-PDF handled gracefully, existing demo flow unaffected, JSON API shapes unchanged, dashboard shows upload link.

### Changed

- **`app/store.py`**: `init_db()` now creates `uploaded_documents` table.
- **`scripts/reset_demo_db.py`**: `PROJECT_TABLES` tuple extended with `"uploaded_documents"` so the reset script drops and re-creates the new table.
- **`requirements.txt`**: added `pypdf==6.11.0` and `python-multipart>=0.0.9`.
- **`.gitignore`**: added `data/uploads/*`, `!data/uploads/.gitkeep`, `data/datasets/*`, `!data/datasets/.gitkeep`.
- **`README.md`**: MVP scope section updated to mention real invoice upload, basic PDF extraction, and the image-OCR limitation. "What it does not do yet" section updated to be explicit about OCR and PDF extraction limitations.
- **`DECISIONS.md`**: D7 added documenting the Phase 2A choices (pypdf, local storage, no OCR yet, regex-only extraction).
- **`app/main.py`**: imports extended (`hashlib`, `uuid`, `File`, `UploadFile`); `_UPLOAD_DIR` added; `_detail_view_model()` extended.

### Tests

```bash
pytest -q
```

```text
......................................                                   [100%]
38 passed in 1.96s
```

### Known limitations

- **Image OCR not implemented.** PNG/JPG uploads store the file and require manual field input. Phase 2B.
- **PDF text extraction is basic.** Works for machine-generated/digital PDFs. Scanned-to-PDF files with no embedded text will produce an `empty` extraction status.
- The upload route uses `agent_id="dashboard_upload_user"` and `user_id="controller_001"` as fixed defaults. These are appropriate for the demo; they would need authenticated-user injection in production.
- Uploaded files are stored on local disk under `data/uploads/`. No serving endpoint exists yet — files are evidence references only.

---

## 2026-06-13 — README and pitch sharpness review (Phase 1D)

Documentation-only pass for GitHub / YC / demo review credibility. **No production code changed. No new dependencies. All 25 tests still pass.**

### Changed

- **`README.md`**:
  - "What it is" rewritten to lead with the infrastructure framing ("ActionRail is infrastructure, not an approval dashboard") and explain why the decisions are structural rather than probabilistic.
  - Added a decision table (4 rows: `allow`, `approval_required`, `blocked`, `needs_more_evidence`) so the machine-readable interface is immediately visible.
  - Added **"What the MVP proves"** section — 6-point numbered summary of what the current primitive demonstrates end-to-end.
  - Added **"Demo narrative"** table — 3 rows showing what each of the three demo flows proves, distinct from the step-by-step browser demo flow.
  - Architecture section now shows the full data-flow as an inline text diagram rather than a flat bullet list.
  - Browser demo flow condensed from 13 steps to 9 (removed intermediate confirmation steps that are implicit in the flow).
  - API demo section condensed — removed redundant sub-headers, folded notes inline, removed the `curl`-without-`jq` variant to reduce noise.
  - "Current MVP scope" rewritten as tighter bullet points without redundant parenthetical elaboration.
  - "What it does not do yet" rewritten with a stronger framing ("deliberate deferments, not oversights").

- **`docs/PITCH.md`**:
  - Added **"What the current MVP proves"** section — 5 numbered concrete points.
  - Added **"Demo narrative"** table parallel to README's.
  - "What is unique" rewritten as 5 sharper bullets: (1) infrastructure not dashboard, (2) transaction primitive not workflow tool, (3) all controls in one layer, (4) deterministic not probabilistic, (5) safety boundary codified not promised.
  - Added **"Why this becomes bigger"** as a standalone section distinct from the roadmap — explains the vertical-agnostic nature with concrete examples (travel, HR, legal, DevOps, commerce).
  - "Future roadmap" section renamed "Roadmap" and tightened.
  - "Demo (90 seconds)" section renamed "Demo narrative" and reformatted as a table matching README.

- **`docs/screenshots/README.md`**: clarified capture step 03 ("after the redirect"; "Reject button gone"); added tip about scrolling to show the stat cards in dashboard screenshots.

- **`.gitignore`**: added `.vscode/` and `.idea/`.

- **`HANDOFF.md`**: removed stale "planned task, not yet present" note about `demo.ps1` (it exists); removed duplicate "Always:" line; pruned stale items from "What to do next" (README and demo.ps1 are done); Phase 1D added to current-state summary.

### Tests

```bash
pytest -q
```

```text
.........................                                                [100%]
25 passed in 1.32s
```

---

## 2026-06-13 — GitHub and demo readiness (Phase 1C)

Repo polish for GitHub / YC / demo review. **No production code changed. No new dependencies. All 25 tests still pass.**

### Added

- **`README.md`** rewritten to GitHub-ready format with the spec'd 12 sections: title, one-line pitch, what it is, why it exists, current MVP scope, what it does not do yet, architecture, project structure, Windows + Linux/macOS quickstart, URLs, browser demo flow (numbered 13-step walkthrough), API demo flow (curl examples for preflight, approve, execute, get receipt, list transactions, plus the duplicate-blocked and missing-evidence preflight cases), safety boundary callout, screenshots placeholder pointing at `docs/screenshots/README.md`, further-reading links, license note. Curl examples include a Windows PowerShell tip to use `curl.exe` rather than the alias.
- **`.gitignore`** at repo root: `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.venv/`, `venv/`, `*.db`, `.env`, `dist/`, `build/`, `.DS_Store`. Local `actionrail.db` is no longer tracked but is preserved on disk.
- **`scripts/demo.ps1`** — guided Windows PowerShell helper. Sets `$ErrorActionPreference = 'Stop'`, resolves the repo root from `$PSScriptRoot`, prints what ActionRail Finance is, restates the simulated-execution safety boundary, runs `pytest -q` (aborts on failure), then prints the next manual commands (`python scripts/reset_demo_db.py`, `uvicorn app.main:app --reload`, the four URLs, and the 11-step browser flow). Non-destructive: never auto-runs the reset script and never auto-launches uvicorn.
- **`docs/`** directory with two new files:
  - **`docs/screenshots/README.md`** — capture flow + naming convention for the 7 canonical demo screenshots (`01-dashboard-clean.png` through `07-missing-evidence.png`), recommended clean state (`reset_demo_db.py` first), tips for clean shots.
  - **`docs/PITCH.md`** — concise YC-style pitch: one-liner ("ActionRail turns risky finance agent actions into safe, auditable transactions."), problem framing, solution (the transaction primitive), why now, first wedge, 90-second demo script, what is unique (agent-first, transaction primitive, evidence + policy + lock + approval + receipt together, vertical-agnostic primitive with finance-first wedge, codified safety boundary), future roadmap aligned to `PROJECT.md` phases 2-6.

### Tests

```bash
pytest -q
```

```text
.........................                                                [100%]
25 passed in 1.30s
```

PowerShell parser check on `scripts/demo.ps1` (via `[System.Management.Automation.Language.Parser]::ParseFile`) reports no syntax errors.

### Known limitations

- README quickstart assumes Python 3.12+ (matches what's installed in dev). No explicit version pin yet.
- `docs/screenshots/` ships with only the README; no actual PNG screenshots are committed yet — that's per the spec ("Do not include actual image files unless already present").
- README has a placeholder license section ("Add your chosen license file before public release"). No `LICENSE` file is committed.
- `scripts/demo.ps1` is non-destructive by design: it runs tests but does not auto-reset the DB or launch uvicorn. Users still need to copy/paste two commands.

---

## 2026-06-13 — Dashboard demo polish (Phase 1B-polish)

Focused polish pass driven by browser review. **No new product scope. No API JSON shape changes. All 25 tests pass.**

### Added

- **Fifth stat card "Needs evidence"** (violet, `.neo-stat--muted`) on `/dashboard`. Counts transactions with `decision == "needs_more_evidence"`. Final order: Total · Approval required · Needs evidence · Blocked · Executed.
- **Recommended demo order** in the empty-state poster: 1) Approval Required Invoice, 2) Duplicate Invoice, 3) Missing Evidence Invoice. Implemented as a styled ordered list (`.neo-empty__list`) so a fresh viewer knows where to click first.
- **Crowded-queue hint**: when the queue holds ≥10 transactions, a small inline note above the table reads `Use scripts/reset_demo_db.py before recording a clean demo.` (CSS class `.neo-queue-note`).
- **Below-table footnote** (CSS class `.neo-queue-note--muted`): `Agent, intent, action, and timestamps are on the transaction detail page.` so reviewers know where the technical detail moved.
- **Compact table variant** (`.neo-table--compact`): smaller cell padding and 0.65rem header font so the simplified table fits typical desktop widths cleanly.
- **`scripts/reset_demo_db.py`** — local-only demo reset. Drops the project's six SQLite tables (`intent_locks`, `transactions`, `invoices`, `contracts`, `vendors`, `policies`) and re-runs `init_db` + `seed_demo`. Importable `reset(db_path=...)` for tests; `main()` entry-point prints a clear, finance-grade success message. Touches only `app.store.DB_PATH`; never deletes arbitrary files; never connects to anything external.
- **`tests/test_reset_demo_db.py`** — 2 tests (clears a populated DB and keeps the seed; idempotent on a fresh DB), both isolated against a `tmp_path` SQLite file via `importlib.util.spec_from_file_location` so the dev DB is never touched.
- **3 new dashboard tests** in `tests/test_dashboard.py`: `test_dashboard_has_needs_evidence_stat_card`, `test_dashboard_table_drops_agent_intent_action_columns`, `test_dashboard_empty_state_lists_recommended_demo_order` (asserts the three example labels appear in the recommended order).

### Changed

- **Dashboard table column set trimmed** from 11 to 7: removed Agent, Intent, Action, and Created from `/dashboard`. Those fields remain on the transaction detail page where the operator/auditor context belongs. Removes the horizontal scroll noted in the browser review.
- `app/main.py` dashboard route now computes a `needs_evidence` count and a `crowded` boolean (true when `total >= 10`) and passes both to the template.
- Empty-state poster body copy now reads "Click one of the demo preflight buttons above to create a real ActionRail transaction." (was a curl invitation in earlier versions).
- `HANDOFF.md` "Run the demo flow" section now leads with the recommended `python scripts/reset_demo_db.py` → `uvicorn app.main:app --reload` flow for screenshot/demo recording.

### Tests

```bash
pytest -q
```

```text
.........................                                                [100%]
25 passed in 1.34s
```

### Known limitations

- The `crowded` threshold is hard-coded at `>= 10`. Easy to tune in `app/main.py` if it shows up too eagerly or too late.
- The reset script does not add a `--yes` confirmation flag; running it always wipes project tables. Acceptable for a local-only demo helper. The README/HANDOFF text emphasises this.
- Running the reset script while uvicorn is live will not crash, but the live `app.main.conn` keeps its handle and any in-memory cached data goes briefly stale until the next request reads from disk. The HANDOFF text recommends stopping uvicorn first.

---

## 2026-06-13 — Dashboard operational flow (Phase 1B)

The browser dashboard is now operationally complete. A user can run the full MVP demo from `/dashboard` without curl or Swagger. Server-rendered HTML forms with `303 See Other` redirects; **no client-side JavaScript added.** Backend logic, API JSON shapes, and existing tests are all preserved.

### Added

- **`POST /dashboard/demo/{example_name}`** — creates a real preflighted transaction from one of three whitelisted example payloads (`approval_required`, `duplicate_blocked`, `missing_evidence`) and `303`-redirects to the new transaction's detail page. Anything not in the whitelist returns `404`. The whitelist is the only mapping from URL segment to disk path, so arbitrary file paths cannot be loaded.
- **`GET /dashboard/transactions/{transaction_id}`** — server-rendered detail page showing transaction ID, agent/user, intent/action, vendor/amount/currency, decision/risk/status badges, allowed-next-action, blocked-actions, all checks (with status badge, message, and evidence JSON per check), evidence URLs, approval/execution panels when present, receipt summary when present, and the raw transaction JSON in a styled `<pre>`.
- **`POST /dashboard/transactions/{transaction_id}/approve`**, **`/reject`**, **`/execute`** — HTML-form endpoints that reuse the same internal helpers as the JSON API. After success, `303` redirect back to the detail page. On rule violation (e.g. executing a blocked txn), the detail page is re-rendered at HTTP `400` with a finance-grade error alert at the top — never a raw JSON dump.
- **`GET /dashboard/transactions/{transaction_id}/receipt`** — server-rendered receipt viewer showing receipt ID, transaction ID, action, status, agent, user, approver, executed-at, full HMAC-SHA256 signature, and the canonical signed payload as JSON. Empty-state copy ("No receipt exists for this transaction yet.") with a back link if the transaction has no receipt.
- **`RUN DEMO PREFLIGHT` section on `/dashboard`** with three side-by-side cards, each holding a server-side form button.
- Vendor and Amount columns + a per-row "View" link on the dashboard table; transaction IDs are now clickable links to the detail page.
- New CSS utilities in `app/static/neo.css` (all keyed off existing tokens, no new colors): `.neo-actions`, `.neo-detail-summary`, `.neo-detail-grid`, `.neo-detail-card` + `__label` / `__value` / `__title` / `__body`, `.neo-demo-grid`, `.neo-pre` (+ `--small`), `.neo-alert` (+ `--error` / `--empty`), `.neo-link-button`, `.neo-receipt`, `.neo-check-list`, `.neo-check-item` (+ status modifiers), `.neo-badge--check-*` for the four `CheckResult` statuses. Mobile breakpoint stacks the action row to full-width buttons.
- New tests in `tests/test_dashboard.py` (15) covering: dashboard list 200 + RUN DEMO PREFLIGHT presence; demo creation for all three examples; invalid demo name → 404; URL path-traversal attempt rejected; detail page 200 with correct decision/status/vendor; detail 404 for unknown id; full happy path approve → execute → receipt; receipt empty state when not yet executed; blocked txn cannot execute; rejected txn cannot execute; needs_more_evidence cannot execute; blocked txn cannot be approved; existing JSON API endpoints still return their original JSON shapes after the helper refactor.

### Changed

- **`app/main.py` refactor**: extracted three small internal helpers (`_approve_transaction`, `_reject_transaction`, `_execute_transaction`) from the existing API route bodies. The JSON API routes are now thin wrappers that call those helpers and return their dict — **API JSON response shapes are byte-identical to before**. The dashboard routes call the same helpers directly. There is now exactly one place in the codebase that owns each state-transition rule.
- Dashboard SQL now also pulls `invoice_json` so the table can render Vendor + Amount columns. Counts query unchanged.
- Migrated three `templates.TemplateResponse(name, {"request": request, …})` calls to the modern `TemplateResponse(request, name, {…})` signature, silencing the Starlette `DeprecationWarning`.

### Tests

```bash
pytest -q
```

```text
....................                                                     [100%]
20 passed in 1.13s
```

### Known limitations

- The dashboard's approve/reject buttons use a fixed `approver_id="dashboard_user"` constant. This is fine for the demo but a real deployment would need authenticated user identity (out of scope until production auth lands; see `PROJECT.md` section 18).
- The dashboard tests monkeypatch `app.main.conn` to a per-test fresh DB. Without that fixture, the persistent intent-lock TTL (15 minutes in `actionrail.db`) would cause serial demo-preflights of the same invoice to land as `decision=blocked`. This is captured in `tests/test_dashboard.py::_isolated_db` and noted in `TASKS.md` testing status.
- No idempotency on duplicate `POST /dashboard/demo/{name}` clicks — each click creates a new transaction. That is intended demo behavior; deferred to a later phase if needed.

---

## [Unreleased] - 2026-06-13 — Dashboard tone calibration (finance-grade)

Reining in the playful neo-brutalism so the dashboard reads as a controlled finance review surface, per `.cursor/rules/actionrail.mdc` rule 9 ("controlled and finance-grade, not a toy"). **Backend untouched. All 5 tests pass.**

### Changed

- `app/static/neo.css`:
  - **Background**: halftone polka-dot radial-gradient → quiet graph-paper grid (`linear-gradient` lines at 6% opacity, 48px cell).
  - **Removed all decorative rotations** from `.neo-logo`, `.neo-tag`, `.neo-empty`, `.neo-empty__commands`, and the corner sticker.
  - **`.neo-empty`** redesigned: plain white card with a 12px yellow left rule + uppercase "Empty queue" label, replacing the rotated yellow poster with a rotated red star sticker.
  - **Renamed `.neo-sticker` → `.neo-stat__pill`** and recolored to neutral black/white (was rotated yellow); class is no longer used in the template after this change.
  - **Semantic palette mapping** for badges (Rule 9): yellow = `approval_required`, red = `blocked` / high risk, violet = `needs_more_evidence` / medium risk, white = neutral/terminal-positive, black = `rejected` / critical risk. Earlier decorative color choices (yellow `allow`, yellow `low`-risk, yellow `approved` status, violet `executed` status) were reassigned to neutral white so colors carry meaning, not decoration.
- `app/templates/dashboard.html`:
  - Removed inline `transform: rotate(...)` styles on the logo and "Finance" word.
  - Stat cards reordered/recolored so **APPROVAL REQUIRED is the yellow card** (was violet) and **TOTAL is neutral white** (was yellow).
  - Removed the rotated "Action!" sticker from the approval-required stat card.
  - Empty-state poster: replaced the rotated `★ Empty Queue ★` star with a flat uppercase `Empty queue` label.

### Tests

```bash
pytest -q
```

```text
.....                                                                    [100%]
5 passed in 0.22s
```

### Rationale

The first-pass neo-brutalist render leaned into the design system's "playful sticker" vocabulary (rotations, polka dots, decorative stickers). That conflicts with `.cursor/rules/actionrail.mdc` rule 9, which was added/expanded since the prior turn. This change keeps every *structural* neo-brutalist signature (thick black borders, hard offset shadows, sharp corners, color blocking, Space Grotesk 900) and drops only the theatrical decoration.

---

## [Unreleased] - 2026-06-13 — Neo-brutalist dashboard

Visual redesign of `/dashboard` in a neo-brutalist style. **Backend logic untouched. All existing tests pass (5/5).**

### Added

- `app/static/neo.css` — single source of truth for neo-brutalist design tokens (cream canvas, pure-black ink, hot red / vivid yellow / soft violet accents, hard offset shadows at 4/8/12/16px, Space Grotesk 900) and utility classes (`.neo-stat`, `.neo-badge`, `.neo-empty`, `.neo-table`, etc.).
- `app/templates/dashboard.html` — Jinja2 template rendering: branded header with rotated sticker logo, four colored stats cards (total / approval required / blocked / executed), an empty-state poster with copy-paste demo curl, and the transaction list as a styled table with colored decision/risk/status sticker badges.
- `Jinja2Templates` and `StaticFiles` mounts in `app/main.py` (under `/static`).
- `jinja2==3.1.4` added to `requirements.txt`.

### Changed

- `GET /dashboard` now renders the Jinja2 template instead of inlining HTML in a Python f-string. Same SQL query for the row list; one extra grouped query for the stat counts. Response shape, status code, and content-type unchanged.

### Decisions

- New decision recorded as **D6** in `DECISIONS.md`: adopt Jinja2 + a single static CSS file for HTML pages. **No Tailwind, no Node, no JS framework.** This was the smallest stack delta that makes the design system maintainable while honoring D4 (dashboard secondary) and D5 (Python-only stack).

### Accessibility

- High-contrast neo-brutalist palette passes WCAG AA on every text/background pairing used.
- `prefers-reduced-motion` disables hover transitions.
- Semantic HTML: `<header>`, `<main>` (via `.neo-shell`), `<section>` with `aria-labelledby`, `<table>` with `<th scope="col">`, `<footer>`. Focus rings are 3px solid black with offset.

### Out of scope (deferred to follow-ups, tracked in `TASKS.md`)

- Transaction detail page (`/transactions/{id}/html`).
- Approve / reject / execute buttons in the dashboard.
- Receipt viewer.
- Preflight demo form.

---

## [0.1.0] - 2026-06-13 — Initial MVP

Phase 0 baseline: the core transaction rail end-to-end on a single laptop, with no real-money side effects.

### Added

- **FastAPI backend** (`app/main.py`) exposing the full preflight → approval → execution → receipt lifecycle.
- **SQLite persistence** (`app/store.py`, `actionrail.db`) with schema and seed data for `vendors`, `contracts`, `invoices`, `policies`, `intent_locks`, `transactions`.
- **Preflight engine** (`app/policy.py`) running the seven core checks: `action_allowed`, `vendor_verified`, `duplicate_invoice`, `contract_match`, `amount_policy`, `evidence_attached`, `intent_lock`.
- **Approval flow**: `POST /approvals/{transaction_id}/approve` and `POST /approvals/{transaction_id}/reject`, gated by transaction state.
- **Execution endpoint**: `POST /actions/{transaction_id}/execute` — simulated only, returns the demo-execution boundary message.
- **Signed receipts**: HMAC-signed receipt payloads exposed via `GET /receipts/{transaction_id}`.
- **HTML dashboard** at `GET /dashboard` with the columns: Transaction | Agent | Intent | Action | Decision | Risk | Status | Created.
- **Agent manifest** at `GET /actionrail/manifest.json` advertising 5 conceptual tools (`preflight_action`, `request_approval`, `execute_transaction`, `get_receipt`, `list_transactions`) and 5 risk levels (`read_only` → `financial_transaction`).
- **CLI prototype** (`app/cli.py`) for agent-style invocation.
- **Example payloads** in `examples/` (approval required, duplicate blocked, missing evidence).
- **Bash demo script** at `scripts/demo.sh` running the full happy-path + duplicate-blocked flow.
- **Tests** (`tests/test_policy.py`) covering: verified vendor large invoice → approval, duplicate blocks, missing contract → needs more evidence, unknown vendor blocks, receipt signature changes with payload.

### Project memory files (this commit)

- Added `TASKS.md`, `DECISIONS.md`, `HANDOFF.md`, `CHANGELOG.md`, and `.cursor/rules/actionrail.mdc` so context survives across Cursor models and chats.

### Safety boundary

- Execution is simulated. No real bank, ERP, or ledger mutations. This boundary is intentional and codified in `DECISIONS.md` (D3) and `PROJECT.md` section 18.

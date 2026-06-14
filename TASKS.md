# TASKS

Working task log for ActionRail Finance. Update this file alongside `HANDOFF.md` and `CHANGELOG.md` after every meaningful change.


- **Phase 5E — Compliance evidence packs, replay, and risk monitoring (done, this commit)**:
  - `app/evidence_pack.py`: ZIP generation with manifest and SHA256 checksums.
  - `app/replay.py`: Policy replay simulation to detect policy differences.
  - `app/store.py`: `save_evidence_export` and `get_transaction_with_audit`.
  - `app/main.py`: New endpoints `/evidence_pack` and `/replay` added.
  - `app/templates/transaction_detail.html`: Risk monitor panel added to UI.
  - Test suites updated with DB state isolation fix.
  - QA Rules updated with Public Website Testing requirements.
  - **Tests: 252/252 passing.**

- **Phase 5C � Approval workflow engine (done, this commit)**:
  - pp/approval_workflow.py: Workflow generation and maker-checker validation logic.
  - pp/main.py: Updated dashboard_approve and dashboard_execute to enforce 2-step rules.
  - pp/templates/transaction_detail.html: UI rendering for workflow status and pending steps.
  - 	ests/test_approval_workflow.py: Comprehensive test suite for Phase 5C.
  - Test suites updated to use updated default policies for isolation.
  - **Tests: 213/213 passing.**

---

## Current MVP goal

Prove the core ActionRail primitive on a single finance wedge:

```text
preflight -> decision -> approval -> execution -> receipt
```

Scope: **invoice approval + duplicate invoice detection**. Execution stays simulated. No real payments, no ERP writeback, no PDF/OCR.

Success looks like:

- `pytest -q` passes.
- Swagger endpoints behave per `PROJECT.md` section 3.
- Demo flows 1-4 (approval required, duplicate blocked, missing evidence, unknown vendor) all behave as documented.

---

## Completed tasks

From the existing repo (Phase 0 in `PROJECT.md` section 20):

- FastAPI app skeleton (`app/main.py`).
- Pydantic request/response models (`app/models.py`).
- Policy engine and decision logic (`app/policy.py`).
- SQLite store + seed data: vendors, contracts, invoices, policies, intent_locks, transactions (`app/store.py`).
- Endpoints live: `/health`, `/actionrail/manifest.json`, `/actions/preflight`, `/transactions`, `/transactions/{id}`, `/approvals/{id}/approve`, `/approvals/{id}/reject`, `/actions/{id}/execute`, `/receipts/{id}`, `/dashboard`.
- Manifest exposes 5 conceptual tools: `preflight_action`, `request_approval`, `execute_transaction`, `get_receipt`, `list_transactions`.
- Checks implemented: `action_allowed`, `vendor_verified`, `duplicate_invoice`, `contract_match`, `amount_policy`, `evidence_attached`, `intent_lock`.
- HMAC-signed receipts.
- Agent-facing CLI prototype (`app/cli.py`).
- Bash demo script (`scripts/demo.sh`).
- Example payloads: approval required, duplicate blocked, missing evidence.
- Tests in `tests/test_policy.py` covering: verified vendor large invoice -> approval, duplicate blocks, missing contract -> needs more evidence, unknown vendor blocks, receipt signature changes with payload.

### Phase 1A — dashboard visual shell (done)

- `/dashboard` redesigned in controlled neo-brutalist style (`app/templates/dashboard.html` + `app/static/neo.css`, no Tailwind/Node/React).
- Tone calibrated to "controlled and finance-grade" per Rule 9: no rotations, quiet graph-paper grid, semantic palette (yellow = approval required, red = blocked/risky, violet = needs_more_evidence/medium risk).
- Stats cards (total / approval required / blocked / executed) and styled transaction list.

### Phase 1B — dashboard operational (done)

- `RUN DEMO PREFLIGHT` section on `/dashboard` with three buttons that POST to `/dashboard/demo/{example_name}` (whitelist of three example payloads).
- Server-rendered transaction detail page at `/dashboard/transactions/{transaction_id}` showing IDs, agent/user, intent/action, vendor/amount, decision/risk/status, checks (with statuses, messages, evidence), evidence URLs, blocked actions, approval/execution/receipt summary, and raw JSON.
- Server-rendered approval/rejection/execute via HTML forms POSTing to `/dashboard/transactions/{id}/approve|reject|execute`. State-aware buttons (Approve/Reject only when `decision=approval_required` and not yet decided; Execute only when execution rules permit).
- `303 See Other` redirects after every POST to prevent accidental resubmission.
- Dashboard execute/approve errors render the detail page with a finance-grade error alert at HTTP 400 instead of dumping raw JSON.
- Server-rendered receipt viewer at `/dashboard/transactions/{id}/receipt` with empty state when no receipt exists.
- Dashboard table includes Vendor, Amount, and View columns; transaction IDs are clickable links to the detail page.
- Backend logic reused via three small internal helpers (`_approve_transaction`, `_reject_transaction`, `_execute_transaction`) that both the JSON API routes and the dashboard routes call. **API JSON response shapes preserved exactly.**

### Phase 1B-polish — dashboard demo readiness (done)

- Dashboard table trimmed to 7 columns: Transaction · Vendor · Amount · Decision · Risk · Status · View. Agent / Intent / Action / Created moved off the executive queue and live only on the transaction detail page. Compact cell padding so the table fits desktop width without horizontal scroll.
- Fifth stat card added: **Needs evidence** (violet, counts `decision == "needs_more_evidence"`). Order: Total · Approval required · Needs evidence · Blocked · Executed.
- Empty-state copy expanded with a recommended demo order (Approval Required → Duplicate → Missing Evidence) so a fresh user knows what to click first.
- When the queue holds 10+ transactions a small inline reset hint appears above the table.
- Local-only demo reset: `scripts/reset_demo_db.py`. Drops the project's six SQLite tables and re-runs `init_db` + `seed_demo`. Importable (`reset(db_path=...)`) for tests; entry-point (`main()`) prints a clear success message. Touches only the local SQLite file at `app.store.DB_PATH`. Run it with uvicorn stopped, then restart uvicorn.

### Phase 1D — README and pitch sharpness review (done)

- `README.md` sharpened: "What it is" now leads with the infrastructure framing ("ActionRail is infrastructure, not an approval dashboard"); added a decision-table for the four decisions; added "What the MVP proves" section (6-point summary of what the primitive demonstrates); added "Demo narrative" table (3 flows × what each proves); browser demo flow condensed to 9 steps; API demo section condensed (removed redundant sub-headers, folded notes inline); architecture section now shows the full data-flow as a text diagram.
- `docs/PITCH.md` sharpened: added "What the current MVP proves" section (5 concrete numbered points); added "Demo narrative" table parallel to README; "What is unique" rewritten with 5 sharper bullets (infrastructure vs dashboard, transaction primitive vs workflow tool, all controls in one layer, deterministic not probabilistic, codified safety boundary); added "Why this becomes bigger" as a standalone section distinct from the roadmap; renamed "Future roadmap" to "Roadmap" and tightened it.
- `docs/screenshots/README.md`: clarified capture step 03 ("after the redirect", "Reject button gone"); added a tip about scrolling to show the stat cards.
- `.gitignore`: added `.vscode/` and `.idea/`.

### Phase 2A-fix2 — Kaggle credential safety and working dataset downloader (done, this commit)

- `.gitignore` extended with `kaggle/`, `kaggle.json`, `**/kaggle.json`, `.kaggle/` — project-local credentials are now gitignored.
- `scripts/download_sample_datasets.py` fully rewritten:
  - Credential detection in priority order: Windows official (`%USERPROFILE%\.kaggle\kaggle.json`) → Linux/macOS official (`~/.kaggle/kaggle.json`) → project-local fallback (`kaggle/kaggle.json`). Project-local fallback prints a warning and sets `KAGGLE_CONFIG_DIR`.
  - `--check-kaggle` flag: prints package availability, credential path (never contents), whether it's inside the repo, setup instructions if missing.
  - `--source kaggle-invoices --instructions` flag: prints the exact Kaggle CLI command.
  - `--source kaggle-invoices --download` flag: runs the kaggle CLI via subprocess; clears pre-flight checks for missing package/credentials; handles `--limit N` to extract a sample subset.
  - `--source funsd --limit N` still works (backward compatible).
  - All existing dataset links preserved; `kaggle-invoices` added as a named source.
- `docs/DATASETS.md` fully updated with: Security section, Kaggle setup on Windows, Kaggle setup on Linux/macOS, Common Kaggle errors troubleshooting table (403, 401, missing creds, not recognized, terms not accepted, not found, ModuleNotFoundError), updated dataset entries, Quick reference command table.
- `tests/test_datasets_script.py` — 7 new offline tests: `--check-kaggle` with no credentials prints setup; project-local credential detection with fake file; `.gitignore` protects `kaggle.json`; `--instructions` prints the correct dataset command; unknown source exits cleanly; `--download` without package exits cleanly; `--download` without credentials exits cleanly.
- **Tests: 45/45 passing.**

### Phase 2B — OCR and dataset sample tooling (done)

- `app/ocr.py`, `scripts/inspect_invoice_dataset.py`, `scripts/prepare_invoice_samples.py`, `docs/OCR.md`, `data/datasets/kaggle-invoices-sample/.gitkeep`. Tests: 56/56.

### Phase 2B-validation — OCR smoke test and extraction improvement (done)

- `scripts/check_ocr.py`, `scripts/run_ocr_sample.py`, `data/datasets/ocr_reports/.gitkeep`, `tests/test_ocr_validation.py` (14 tests). Tests: 70/70.

### Phase 2F — Final demo packaging and public repo hygiene (done)

- `LICENSE` (MIT), `docs/RELEASE_CHECKLIST.md`, README/PITCH/screenshots doc updates. No code changes. Tests: 123/123.

### Phase 3A — Accounting sandbox writeback foundation (done, this commit)

- `app/accounting.py` (new) — `AccountingDraftBill`, `AccountingAuditPacket`, `AccountingWritebackResult` Pydantic models; `LocalAccountingSandboxAdapter.create_draft_bill()` that validates executed+receipt, writes draft bill and audit packet JSON to `data/accounting_sandbox/`, returns relative paths only.
- `app/store.py` — `accounting_writebacks` table + `save_accounting_writeback()` (idempotent), `get_accounting_writeback()`, `list_accounting_writebacks()`.
- `scripts/reset_demo_db.py` — `accounting_writebacks` added to `PROJECT_TABLES`.
- `app/main.py` — `POST/GET /dashboard/transactions/{id}/writeback/accounting-sandbox`.
- `app/templates/accounting_writeback.html` (new) — sandbox writeback page.
- `app/templates/transaction_detail.html` — writeback button when executed.
- `data/accounting_sandbox/` directories + `.gitkeep`.
- `.gitignore` updated. `README.md`, `docs/PITCH.md`, `docs/RELEASE_CHECKLIST.md` updated.
- **Tests: 136/136 passing.**

### Phase 3B — Accounting writeback validation, UX polish, demo hardening (done, this commit)

- **`app/templates/accounting_writeback.html`**: clearer safety copy; shows transaction ID, provider, status, draft bill ID, created at, `local://` references (no absolute paths); collapsible draft bill and audit packet JSON.
- **`app/templates/transaction_detail.html`**: conditional Create vs View writeback buttons; dedicated accounting sandbox section with boundary copy.
- **`app/main.py`**: `has_accounting_writeback` passed to detail template; writeback GET loads artifacts via adapter dirs; `draft_bill_ref` / `audit_packet_ref` as `local://` URIs; `_ACCOUNTING_PROVIDER` moved to module top.
- **`tests/test_accounting.py`**: 5 new tests (141 total): create vs view button logic, idempotent POST, no absolute paths, draft bill receipt signature, audit packet checks+receipt.
- **`README.md`**, **`docs/RELEASE_CHECKLIST.md`**, **`docs/screenshots/README.md`**: full writeback demo flow + optional screenshot `12-accounting-sandbox-writeback.png`.
- Receipt payload unchanged (no writeback in signed receipt).
- **Tests: 141/141 passing.**

### Phase 3C — Final transaction state polish and screenshot readiness (done, this commit)

- **`app/main.py`**: `_display_next_ui_action()` and `_transaction_state_summary()` — UI-only display fields; stale stored `allowed_next_action` no longer shown in overview after execution.
- **`app/templates/transaction_detail.html`**: "Next UI action" overview field; state summary banner (executed/blocked/approval-required); existing Create/View writeback buttons unchanged.
- **`tests/test_accounting.py`**: 5 new Phase 3C tests (146 total): next action per state, state summary copy, button Create→View transition.
- **`README.md`**, **`docs/screenshots/README.md`**: screenshot `13-executed-transaction-with-writeback.png` + capture notes.
- **Tests: 146/146 passing.**

### Phase 3D — Dashboard stat correctness polish (done, this commit)

- **`app/main.py`**: `_compute_dashboard_stats()` — stat cards count current operational state (approval required = preflighted only; executed excludes from approval stat).
- **`tests/test_dashboard.py`**: 8 new Phase 3D tests (154 total): unit tests for stat helper + integration tests via dashboard HTML.
- **Tests: 154/154 passing.**

### Phase 4A — Final MVP completion and public release polish (done, this commit)

- **`app/templates/dashboard.html`**: queue table column renamed to **Preflight Decision**.
- **`tests/test_dashboard.py`**: test for Preflight Decision column header.
- **New docs**: `docs/DEMO_SCRIPT.md`, `docs/ARCHITECTURE.md`, `docs/SAFETY_BOUNDARY.md`, `docs/PROJECT_COMPLETION.md`.
- **`README.md`**: completion status section + links to new docs.
- **`docs/RELEASE_CHECKLIST.md`**: GitHub repo polish checklist + git hygiene commands.
- **`docs/screenshots/README.md`**: canonical 01–13 list + optional-for-tests note.
- **Tests: 155/155 passing.**

### Phase 5A — Authenticated control plane (done, this commit)

- **`app/auth.py`**, **`app/control.py`**: local PBKDF2 auth, six roles, RBAC, CSRF, audit helpers.
- **`app/store.py`**: `users`, `audit_events` tables + helpers; demo users seeded idempotently.
- **`app/main.py`**: SessionMiddleware, login/logout/audit routes, protected dashboard routes, audit events.
- **Templates**: login, forbidden, audit log, control nav partial; CSRF on all dashboard POST forms.
- **`scripts/reset_demo_db.py`**: resets users + audit_events.
- **`tests/test_auth.py`**, **`tests/dash_helpers.py`**; existing dashboard tests updated for auth/CSRF.
- **Docs** updated (README demo credentials, ARCHITECTURE, SAFETY_BOUNDARY, DEMO_SCRIPT, etc.).
- **Tests: 196/196 passing.**

### Phase 5B — Policy admin, vendor onboarding, contract evidence (done, this commit)

- **Phase 5B — Policy admin, vendor onboarding, contract evidence (done)**:
  - `app/admin_routes.py`: admin dashboard routes (vendors, contracts, policies, evidence upload).
  - `app/store.py`: schema migration, vendor/contract CRUD, policy update, contract evidence helpers.
  - `app/policy.py`: vendor status + contract status/expiry checks.
  - `app/auth.py`: `manage_admin` permission.
  - Templates: `admin_*.html` (6 files).
  - `data/contract_evidence/`, `.gitignore` updated.
  - `tests/test_admin.py`: 21 new tests.
  - **Tests: 196/196 passing.**

- **Context-retention and handoff pass (done)**: verified state, created `docs/ANTIGRAVITY_HANDOFF.md`, `docs/ROUTE_MAP.md`, `docs/SCHEMA_MAP.md`, and `docs/NEXT_PHASE_5C_PROMPT.md`.

---

## Next tasks

Priority order:

1. **Phase 5C — Approval workflow engine** (see `docs/NEXT_PHASE_5C_PROMPT.md`): multi-step workflows, maker-checker separation, and execution gating.

2. **Expand backend-policy tests** (per `PROJECT.md` section 16) — backend-policy items not yet covered:
   - Executed transaction returns same receipt idempotently.
   - Intent lock blocks second transaction for same invoice; expired lock cleaned up.
   - Action not in `allowed_actions` is blocked.
   - GST mismatch creates warning.
   - Contract amount exceeded blocks.
   - Critical amount requires senior approval.
   - Receipt signature verifies with secret.
   - Policy update changes decision.

3. **Phase 2B — Image OCR**: Add Tesseract / PaddleOCR / EasyOCR support for scanned image invoices.

4. Clean up `app/cli.py` to expose: health, manifest, approve, reject, execute, receipt, transactions, dashboard.

5. Capture and commit the 7 demo screenshots per `docs/screenshots/README.md`.

6. Pick a license and add a `LICENSE` file before public release.

---

## Blocked tasks

None right now. Future phases (real ingestion, integrations, MCP server, payments) are deferred — see `DECISIONS.md`.

---

## Testing status

- Test runner: `pytest -q`.
- Last known state (2026-06-14, after Context-retention pass): **196 / 196 tests pass**.
- Dashboard tests use an autouse fixture that monkeypatches `app.main.conn` to a fresh per-test SQLite DB seeded with demo data. Without isolation, the persistent intent-lock TTL (15 minutes) makes serial demo-preflights of the same invoice land as `decision=blocked`.
- **Rule**: do not remove tests. Add new tests under `tests/` for every new policy/transaction behavior.

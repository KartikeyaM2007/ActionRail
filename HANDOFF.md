# HANDOFF

Living handoff doc for the next Cursor model/chat picking up ActionRail Finance. Read this **after** `PROJECT.md` and **before** touching code. Update this file at the end of every session.

---

## Current project state

- Phase 0 MVP per `PROJECT.md` section 20 is in place and runnable.
- FastAPI app, SQLite store with seed data, policy engine, approval/execute/receipt flow, signed receipts.
- **Phase 1A — visual shell (done)**: `/dashboard` redesigned in a controlled neo-brutalist style (Jinja2 + `app/static/neo.css`, no Tailwind/Node/React). Tone calibrated to "finance-grade" per Rule 9 — no rotations, quiet graph-paper grid, semantic palette (yellow=approval required, red=blocked/risky, violet=needs_more_evidence/medium risk).
- **Phase 1B — operational dashboard (done)**: a user can complete the full demo from the browser without curl/Swagger. `/dashboard` has a `RUN DEMO PREFLIGHT` section with three buttons. Transaction IDs are clickable. New routes: `POST /dashboard/demo/{name}`, `GET /dashboard/transactions/{id}`, `POST /dashboard/transactions/{id}/approve|reject|execute`, `GET /dashboard/transactions/{id}/receipt`. All server-rendered HTML forms, `303 See Other` redirects after every POST, no client-side JS. State-aware action buttons (Approve/Reject only when `decision=approval_required`; Execute only when execution rules permit; View Receipt only when a receipt exists).
- **Phase 1B-polish (done)**: dashboard table trimmed to 7 executive columns (Transaction · Vendor · Amount · Decision · Risk · Status · View) with compact padding so it fits desktop width. Fifth violet stat card "Needs evidence" added. Empty state lists recommended demo order. When the queue has ≥10 transactions, a small inline hint suggests `scripts/reset_demo_db.py`.
- **Demo reset script**: `scripts/reset_demo_db.py` drops the project's SQLite tables and re-seeds. Local-only. Run with uvicorn stopped, then restart uvicorn.
- **Phase 1C — GitHub and demo readiness (done)**: README.md rewritten to GitHub-ready format; `.gitignore` added; `scripts/demo.ps1` guided PowerShell helper; `docs/screenshots/README.md` capture flow; `docs/PITCH.md` concise YC pitch. **No production code changed.**
- **Phase 1D — README and pitch sharpness review (done)**: README sharpened with infrastructure framing, decision table, "What the MVP proves" section, "Demo narrative" table, condensed API section. `docs/PITCH.md` sharpened with "What the current MVP proves", "Demo narrative", rewritten "What is unique" bullets, new "Why this becomes bigger" section. `docs/screenshots/README.md` minor wording. `.gitignore` extended with `.vscode/` and `.idea/`. **No production code changed. Tests unchanged at 25/25.**
- **Phase 2A-fix2 — Kaggle credential safety and working dataset downloader (done)**: `.gitignore` extended with `kaggle/`, `kaggle.json`, `**/kaggle.json`, `.kaggle/`. `scripts/download_sample_datasets.py` fully rewritten with credential detection (3-level priority), `--check-kaggle`, `--instructions`, `--download`, `--limit` flags. `docs/DATASETS.md` updated with Kaggle setup for Windows + Linux, troubleshooting table. `tests/test_datasets_script.py` — 7 offline tests. **No production code changed. Tests: 45/45 passing.**
- **Phase 2F — Final demo packaging and public repo hygiene (done)**: `LICENSE` (MIT), `docs/RELEASE_CHECKLIST.md`, doc updates. No code changes. Tests: 123/123 passing.
- **Phase 3A — Accounting sandbox writeback foundation (done)**: `app/accounting.py` (new models + `LocalAccountingSandboxAdapter`); `accounting_writebacks` table in SQLite; `POST/GET /dashboard/transactions/{id}/writeback/accounting-sandbox`; `app/templates/accounting_writeback.html` with safety banner; transaction detail shows writeback button when executed; `data/accounting_sandbox/` directories. **Tests: 136/136 passing.**
- **Phase 3B — Accounting writeback validation, UX polish, demo hardening (done)**: writeback page clarity (safety copy, `local://` refs, collapsible JSON); transaction detail shows Create vs View writeback buttons conditionally; 5 new accounting tests; docs updated with full writeback demo flow and optional screenshot `12-accounting-sandbox-writeback.png`. Receipt unchanged. **Tests: 141/141 passing.**
- **Phase 3C — Final transaction state polish and screenshot readiness (done)**: `_display_next_ui_action()` fixes stale `request_finance_approval` in overview after execution; state summary banner on transaction detail; screenshot `13-executed-transaction-with-writeback.png` documented. **Tests: 146/146 passing.**
- **Phase 3D — Dashboard stat correctness polish (done)**: `_compute_dashboard_stats()` — executed transactions no longer inflate Approval Required stat; approval required counts only `decision=approval_required` + `status=preflighted`. **Tests: 154/154 passing.**
- **Phase 4A — Final MVP completion and public release polish (done)**: dashboard column **Preflight Decision**; new docs (`DEMO_SCRIPT`, `ARCHITECTURE`, `SAFETY_BOUNDARY`, `PROJECT_COMPLETION`); README completion status; GitHub release checklist. **Tests: 155/155 passing.**
- Backend logic reused via three small internal helpers (`_approve_transaction`, `_reject_transaction`, `_execute_transaction`) shared by the JSON API routes and the dashboard routes. **API JSON response shapes preserved exactly.**
- **Phase 5A — Authenticated control plane (done)**: local dashboard login (`/login`), six demo roles with RBAC, CSRF on dashboard POST forms, audit ledger (`/dashboard/audit`), transaction-level audit trail on detail pages. JSON API unchanged. **Tests: 175/175 passing.**
- **Phase 5B — Policy admin, vendor onboarding, contract evidence (done)**: admin UI at `/dashboard/admin` for vendors, contracts, policy thresholds, contract evidence upload. All admin changes audited. **Tests: 196/196 passing.**
- **Context-retention and handoff pass (done)**: verified state, created `docs/ANTIGRAVITY_HANDOFF.md`, `docs/ROUTE_MAP.md`, `docs/SCHEMA_MAP.md`, and `docs/NEXT_PHASE_5C_PROMPT.md`.
- No other work-in-progress.

---

## How to run the project

From the repo root: `e:\actionrail-finance-mvp-with-project-md\actionrail-finance`.

### 1. Create and activate a virtual environment

PowerShell (Windows):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

bash (Linux/macOS):

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run tests

```bash
pytest -q
```

This must pass before and after any backend change.

### 4. Start the API

```bash
uvicorn app.main:app --reload
```

Open in browser:

- `http://127.0.0.1:8000/login` — dashboard sign-in (demo credentials in README)
- `http://127.0.0.1:8000/docs` — Swagger / OpenAPI
- `http://127.0.0.1:8000/dashboard` — HTML dashboard (requires login)
- `http://127.0.0.1:8000/dashboard/admin` — vendor/contract/policy admin (admin only)
- `http://127.0.0.1:8000/dashboard/audit` — audit log (auditor/admin)
- `http://127.0.0.1:8000/actionrail/manifest.json` — agent manifest

Optional: set `ACTIONRAIL_SESSION_SECRET` for non-dev sessions (dev fallback exists with warning in code).

### 5. Run the demo flow

Recommended for clean screenshots (any platform):

```bash
# Stop uvicorn first if it's running.
python scripts/reset_demo_db.py
uvicorn app.main:app --reload
# Open http://127.0.0.1:8000/dashboard and click the demo buttons in order:
#   1. Approval Required Invoice
#   2. Duplicate Invoice
#   3. Missing Evidence Invoice
```

Or run the canonical bash demo script:

```bash
bash scripts/demo.sh
```

Or run the guided PowerShell demo script (Windows):

```powershell
pwsh scripts/demo.ps1
```

Or call the CLI directly:

```bash
python -m app.cli preflight examples/invoice_approval_required.json
python -m app.cli preflight examples/invoice_duplicate_blocked.json
python -m app.cli preflight examples/invoice_missing_evidence.json
```

If the dashboard is empty, post to `/actions/preflight` from Swagger or run the demo first — transactions only appear once preflighted.

---

## Important files

| Path | Role |
|---|---|
| `docs/ANTIGRAVITY_HANDOFF.md` | Antigravity handoff document covering project state and architecture. |
| `docs/ROUTE_MAP.md` | Current route map detailing all public, dashboard, and API endpoints. |
| `docs/SCHEMA_MAP.md` | Current schema map detailing all SQLite tables. |
| `docs/NEXT_PHASE_5C_PROMPT.md` | Future prompt for Phase 5C (Approval Workflow Engine). |
| `PROJECT.md` | Master product/architecture spec. Always read first. |
| `README.md` | User-facing quickstart and API summary. |
| `LICENSE` | MIT License. |
| `docs/RELEASE_CHECKLIST.md` | Pre-release checklist — run before pushing. |
| `TASKS.md` | Current goal, completed/next/blocked work, testing status. |
| `DECISIONS.md` | Why-decisions: finance first, MVP scope, no real payments, dashboard secondary, tech stack. |
| `HANDOFF.md` | This file. Current state + how to run + what to do next. |
| `CHANGELOG.md` | Versioned log of changes. Update on every change. |
| `.cursor/rules/actionrail.mdc` | Always-applied agent rules for this repo. |
| `app/main.py` | FastAPI routes. Keep business logic out; delegate to `policy.py` / `store.py`. |
| `app/models.py` | Pydantic request/response schemas. |
| `app/policy.py` | Preflight checks, decision logic, receipt signing. Core of the rail. |
| `app/store.py` | SQLite schema, seed data, query helpers. |
| `app/cli.py` | Agent-facing CLI prototype. |
| `app/templates/dashboard.html` | Jinja2 template for the neo-brutalist `/dashboard` (header, stats, RUN DEMO PREFLIGHT section, transaction table). |
| `app/accounting.py` | Accounting sandbox models + `LocalAccountingSandboxAdapter`. |
| `app/templates/accounting_writeback.html` | Sandbox writeback page with safety banner, collapsible JSON blocks. |
| `app/templates/receipt.html` | Jinja2 template for `/dashboard/transactions/{id}/receipt` (or finance-grade empty state if no receipt). |
| `app/static/neo.css` | Neo-brutalist design tokens + utility classes. **Single source of truth** for the visual language. |
| `tests/test_policy.py` | Existing policy and receipt tests. Do not remove. |
| `tests/test_dashboard.py` | Dashboard-route tests (Phase 1B + polish). Uses an autouse fixture that gives each test a fresh SQLite DB. |
| `scripts/evaluate_invoice_extraction.py` | CSV-only extraction evaluator (no OCR/images). Reports coverage across 5 fields. |
| `tests/test_extraction_safety.py` | 24 offline tests for currency/amount safety, upload route behavior. |
| `scripts/run_ocr_sample.py` | Runs OCR on sample folder images; prints extraction results; optional JSON report. |
| `data/datasets/ocr_reports/.gitkeep` | OCR reports directory tracked in git; report files gitignored. |
| `tests/test_ocr_validation.py` | 14 offline tests for check/run scripts, USD extraction, existing flows. |
| `tests/test_datasets_script.py` | 7 offline tests for the dataset downloader script. |
| `tests/test_upload.py` | Upload flow tests: page load, invalid extension, PNG upload with manual fields, PDF SHA-256 and evidence ref, missing-fields 400, extraction helpers, existing demo flow unaffected, JSON API shapes, dashboard upload link. |
| `tests/test_reset_demo_db.py` | Tests for the demo reset script. Uses `tmp_path`; never touches the dev DB. |
| `scripts/reset_demo_db.py` | Local-only demo reset. Drops project tables in the SQLite DB and re-seeds. Importable `reset(db_path=…)` + `main()` entry point. |
| `scripts/demo.ps1` | Guided Windows PowerShell demo. Runs pytest, prints the next manual commands. Non-destructive. |
| `app/ocr.py` | Optional OCR via pytesseract. Graceful fallback when missing. Never required. |
| `app/extraction.py` | PDF text extraction (pypdf) and regex-based field extractor. |
| `data/uploads/.gitkeep` | Keeps the upload directory tracked in git while files are gitignored. |
| `data/datasets/.gitkeep` | Keeps the datasets directory tracked in git while datasets are gitignored. |
| `docs/DATASETS.md` | Reference list of 6 invoice/receipt datasets with links and license notes. |
| `scripts/download_sample_datasets.py` | Prints dataset links; can optionally download a FUNSD sample. |
| `scripts/inspect_invoice_dataset.py` | Prints Kaggle dataset structure without loading images into memory. |
| `scripts/prepare_invoice_samples.py` | Copies N invoice images to `data/datasets/kaggle-invoices-sample/` for OCR testing. |
| `docs/screenshots/README.md` | Capture flow and naming convention for the 7 canonical demo screenshots. |
| `.gitignore` | Excludes `__pycache__`, `.venv/`, `*.db`, `.env`, build artefacts, OS files. |
| `examples/*.json` | Canonical demo payloads. |
| `scripts/demo.sh` | Bash end-to-end demo script. |
| `actionrail.db` | SQLite database file (auto-created/seeded on startup). Safe to delete to reset. |
| `requirements.txt` / `pyproject.toml` | Dependency manifests. |

---

## Current endpoints

JSON API (unchanged response shapes):

```text
GET  /health
GET  /actionrail/manifest.json
POST /actions/preflight
GET  /transactions
GET  /transactions/{transaction_id}
POST /approvals/{transaction_id}/approve
POST /approvals/{transaction_id}/reject
POST /actions/{transaction_id}/execute
GET  /receipts/{transaction_id}
```

Server-rendered dashboard (HTML; HTML forms post here, 303 redirects after):

```text
GET  /dashboard
POST /dashboard/demo/{example_name}             # whitelist: approval_required | duplicate_blocked | missing_evidence
GET  /dashboard/transactions/{transaction_id}
POST /dashboard/transactions/{transaction_id}/approve
POST /dashboard/transactions/{transaction_id}/reject
POST /dashboard/transactions/{transaction_id}/execute
GET  /dashboard/transactions/{transaction_id}/receipt
POST /dashboard/transactions/{transaction_id}/writeback/accounting-sandbox   # create sandbox draft bill (executed only; idempotent)
GET  /dashboard/transactions/{transaction_id}/writeback/accounting-sandbox   # view writeback page
GET  /dashboard/invoices/upload
POST /dashboard/invoices/upload
GET  /dashboard/invoices/review/{doc_id}
POST /dashboard/invoices/review/{doc_id}/submit
GET  /dashboard/audit
GET  /dashboard/admin
GET  /dashboard/admin/vendors
POST /dashboard/admin/vendors
GET  /dashboard/admin/vendors/{vendor_id}
POST /dashboard/admin/vendors/{vendor_id}/update
GET  /dashboard/admin/contracts
POST /dashboard/admin/contracts
GET  /dashboard/admin/contracts/{contract_id}
POST /dashboard/admin/contracts/{contract_id}/update
POST /dashboard/admin/contracts/{contract_id}/evidence
GET  /dashboard/admin/policies
POST /dashboard/admin/policies
```

Decisions returned by `/actions/preflight`: `allow`, `approval_required`, `blocked`, `needs_more_evidence`.

Statuses on transactions: `preflighted`, `approved`, `rejected`, `executed`, `blocked`.

---

## What to do next

In priority order (mirrors `TASKS.md`):

1. **Phase 5C — Approval workflow engine** (see `docs/NEXT_PHASE_5C_PROMPT.md`): multi-step workflows, maker-checker separation, and execution gating.
2. **Expand backend-policy tests** (per `PROJECT.md` section 16) — idempotent receipt, intent-lock conflict + expiry, action-not-in-allowed_actions, GST mismatch, contract overflow, critical-amount senior approval.
3. **Capture demo screenshots** per `docs/screenshots/README.md` (7 core + 4 real-upload + optional writeback `12` + post-writeback detail `13`).
4. **Push to GitHub** — run through `docs/RELEASE_CHECKLIST.md` first.
5. Clean up `app/cli.py`.

Always: after edits, run `pytest -q`, then update this file, `CHANGELOG.md`, and append a new entry to `ForKnow.md`.

---

## What not to change

These are settled decisions (see `DECISIONS.md`). Do not change them without an explicit user request that overrides:

- **Do not add real payment execution.** Execution stays simulated; the literal demo response string is part of the safety boundary.
- **Do not remove or weaken existing tests.** Add tests, don't subtract.
- **Do not move business logic into route handlers or HTML.** It belongs in `app/policy.py` / `app/store.py`.
- **Do not pivot away from the agent-first framing.** Machine-readable API responses are the primary interface; dashboard is secondary.
- **Do not introduce real bank/ERP/email/OCR integrations** without a task that explicitly asks for it. Phase 5 in `PROJECT.md` is deferred.
- **Do not swap the stack** (FastAPI / SQLite / Pydantic / pytest / HMAC receipts; plus Jinja2 + `app/static/neo.css` for HTML pages per D6) without a decision recorded in `DECISIONS.md`.
- **Do not introduce Tailwind, Node, or a JS framework** for the dashboard. The neo-brutalist tokens live in `app/static/neo.css` as CSS custom properties (D6). New pages should reuse those utilities, not bring a new toolchain.
- **Do not touch `PROJECT.md`** — it is the spec, not a working doc.
- **Do not delete `actionrail.db` as part of code changes**; let users reset it themselves if they want a clean state.

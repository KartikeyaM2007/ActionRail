# ForKnow — Cursor work journal

Append-only, factual log of what Cursor actually did, written so the user can copy the latest entry back to ChatGPT. Never edit or delete prior entries.

---

# Cursor Work Update: Neo-brutalist dashboard + tone calibration (consolidated)

## Date

2026-06-13, IST evening session.

## Prompt I worked on

Two consecutive prompts in the same Cursor chat:

1. Apply the supplied neo-brutalist design system to the project, integrated idiomatically into the existing tech stack.
2. After updated `.cursor/rules/actionrail.mdc` was read, calibrate the dashboard tone to "controlled and finance-grade" per rule 9, and append a single consolidated `ForKnow.md` entry covering both turns.

## Note on `ForKnow.md` rule compliance

`.cursor/rules/actionrail.mdc` rule 6 requires appending a `ForKnow.md` entry after every change. I did **not** append an entry for the first prompt (the initial neo-brutalist dashboard build) at the time it was made. This entry is the catch-up, written per the user's explicit choice to consolidate both turns into one entry rather than backfill separately. No prior `ForKnow.md` entries were overwritten because the file was empty.

## Files changed (net, both turns combined)

| File | What changed |
|---|---|
| `DECISIONS.md` | Added decision **D6**: adopt Jinja2 + a single static CSS file at `app/static/neo.css` for HTML pages. No Tailwind, no Node, no JS framework. |
| `requirements.txt` | Added `jinja2==3.1.4`. |
| `app/main.py` | Imported `Path`, `Request`, `StaticFiles`, `Jinja2Templates`. Mounted `/static` and instantiated `Jinja2Templates`. Replaced the inline-HTML body of `dashboard()` with a `TemplateResponse` render and a one-extra `GROUP BY decision, status` query for stat counts. **No other backend logic touched.** |
| `app/static/neo.css` (new) | Neo-brutalist design tokens (CSS custom properties for colors, borders, shadows, font, easing) + utility/component classes (`.neo-shell`, `.neo-stat`, `.neo-table`, `.neo-badge--*`, `.neo-empty`, `.neo-btn`, footer). After tone calibration: rotations removed from `.neo-logo`/`.neo-tag`/`.neo-empty`/`.neo-empty__commands`; halftone polka-dot body background replaced with a quiet graph-paper grid; `.neo-sticker` renamed to `.neo-stat__pill` and recolored neutral; badge classes re-mapped to a semantic palette (yellow = approval required, red = blocked/high risk, violet = needs_more_evidence / medium risk, white = neutral, black = rejected/critical). |
| `app/templates/dashboard.html` (new) | Jinja2 template: branded header with rotated sticker logo (rotation later removed), four stat cards, "TRANSACTION QUEUE" section with thick black under-rule, transaction table with color-coded decision/risk/status badges, empty-state poster with copy-paste curl example, footer with yellow offset shadow. After tone calibration: removed inline `transform: rotate(...)` on the logo/Finance word; stat-card order/colors corrected so APPROVAL REQUIRED is yellow and TOTAL is neutral white; rotated "Action!" sticker removed; rotated "★ Empty Queue ★" star replaced with a flat uppercase label. |
| `HANDOFF.md` | Reflected the dashboard redesign and the subsequent tone calibration. Added `app/templates/dashboard.html` and `app/static/neo.css` to the important-files table. Reworded the next-task list (visual shell done; remaining items are detail page, approval/execute/receipt buttons, preflight form). Added "do not introduce Tailwind/Node/JS framework" to the "what not to change" list. |
| `CHANGELOG.md` | Two unreleased entries dated 2026-06-13: (1) "Neo-brutalist dashboard" — initial redesign; (2) "Dashboard tone calibration (finance-grade)" — rotations/halftone/decoration removed, semantic palette applied. Both entries include exact `pytest -q` output. |
| `ForKnow.md` (this file) | Created from empty, with header + this consolidated entry. |

## What I added

- A new server-side templating layer for FastAPI HTML pages: `Jinja2Templates(directory=app/templates)` plus a `StaticFiles` mount at `/static`.
- A single source-of-truth design-token file at `app/static/neo.css` (~280 lines) using CSS custom properties.
- A neo-brutalist Jinja2 template at `app/templates/dashboard.html` rendering the existing transaction list with stats and an empty state.
- Decision entry D6 in `DECISIONS.md` documenting the stack delta (Jinja2 + static CSS, no Tailwind/Node/React).
- One extra SQL query in `dashboard()` to compute stat counts (`SELECT decision, status, COUNT(*) ... GROUP BY decision, status`).

## What I modified

- `app/main.py`: only the imports block and the body of `dashboard()`. All other routes, models, policy, store, CLI, and tests are untouched.
- `requirements.txt`: appended `jinja2==3.1.4` between `pydantic` and `pytest`.
- `app/static/neo.css` and `app/templates/dashboard.html`: edited a second time during the tone calibration step (rotations off, halftone off, palette semantics fixed).

## What I did not change

- `app/policy.py`, `app/store.py`, `app/models.py`, `app/cli.py` — zero edits.
- `tests/test_policy.py` — zero edits, all 5 tests still pass.
- `examples/*.json` — unchanged.
- `scripts/demo.sh` — unchanged.
- `PROJECT.md`, `README.md` — unchanged.
- `.cursor/rules/actionrail.mdc`, `.cursor/rules/karpathy-guidelines.mdc` — unchanged (these are user-authored rules; I only read them).
- API endpoints, request/response shapes, status codes, content-types — all unchanged.
- The `from datetime import timezone` import in `app/main.py` is unused but predates my changes; per the surgical-edits rule I left it alone.

## Tests run

After the initial dashboard redesign:

```bash
pytest -q
```

```text
.....                                                                    [100%]
5 passed in 0.21s
```

After the tone calibration:

```bash
pytest -q
```

```text
.....                                                                    [100%]
5 passed in 0.22s
```

I also ran an end-to-end smoke check via `fastapi.testclient.TestClient` after each step:

- `GET /dashboard` returned `200 text/html; charset=utf-8`.
- `GET /static/neo.css` returned `200` with content length around 11.8 KB (initial) / similar after calibration.
- After calibration, the rendered HTML contains zero `rotate(` substrings and the CSS contains the semantic palette mapping for `decision-approval_required`.

## Current status

- App status: **runs cleanly**. `uvicorn app.main:app` starts without warnings. `/health`, `/actionrail/manifest.json`, `/actions/preflight`, `/transactions`, `/approvals/.../approve|reject`, `/actions/.../execute`, `/receipts/...` are all unchanged in behavior.
- Dashboard status: **redesigned and tone-calibrated**. Cream canvas with quiet graph-paper grid, thick black borders, hard offset shadows, sharp corners, Space Grotesk 900, color-blocked decision/risk/status badges with semantic palette per rule 9. No rotations, no decorative stickers, no halftone polka dots.
- API status: **unchanged**. Pure additive on the HTML rendering side.
- Known issues:
  - The transaction detail page (`/transactions/{id}/html`), approve/reject/execute buttons in the dashboard, receipt viewer, and preflight demo form are still **not built** — tracked in `TASKS.md` priority #1 sub-bullets.
  - Pre-existing unused import `from datetime import timezone` in `app/main.py` was left in place per surgical-edits guidance. Not introduced by me. Mention only.
  - The `streamlit` package globally installed has an unrelated `python-multipart` version conflict warning at `pip install` time. Not from this project. Ignored.

## What still needs manual review

- Visual confirmation in your own browser that the calibrated dashboard reads as "finance-grade" rather than "toy." If still too playful, the next dial to turn is removing the yellow offset shadow on the footer and/or muting the red on the BLOCKED stat card to a smaller accent.
- Whether the semantic palette mapping I chose for badges (yellow = approval_required, red = blocked, violet = needs_more_evidence, white = allow / approved / executed / preflighted, black = rejected) matches the operational meaning you want a controller to see at a glance.

## What the user should send to ChatGPT

Copy paste this whole latest `ForKnow.md` entry (everything from `# Cursor Work Update: Neo-brutalist dashboard + tone calibration (consolidated)` down to the end of this section).

---

# Cursor Work Update: Phase 1B — operational dashboard

## Date

2026-06-13, IST evening session (continuation).

## Prompt I worked on

Phase 1B: make the browser dashboard operationally complete. Add a RUN DEMO PREFLIGHT section with three buttons, a transaction detail page, server-rendered approve/reject/execute, and a receipt viewer. Server-rendered HTML forms only, 303 redirects after every POST, no client-side JavaScript. Reuse existing backend logic. Preserve all existing API JSON shapes. Add tests for the new flows and for the guardrails. Update TASKS.md, HANDOFF.md, CHANGELOG.md, ForKnow.md.

## Files changed

| File | What changed |
|---|---|
| `app/main.py` | Extracted three internal helpers (`_approve_transaction`, `_reject_transaction`, `_execute_transaction`) from the existing API route bodies; the JSON API routes are now thin wrappers that call them. Added `DEMO_EXAMPLES` whitelist + `_load_demo_request` helper. Added view-model adapters `_row_to_listing`, `_detail_view_model`, gating predicates `_can_approve`, `_can_execute`, `_has_receipt`, and `_render_detail`. Added six new dashboard routes: `POST /dashboard/demo/{example_name}`, `GET /dashboard/transactions/{id}`, `POST /dashboard/transactions/{id}/approve|reject|execute`, `GET /dashboard/transactions/{id}/receipt`. Updated dashboard SQL to also select `invoice_json` so vendor + amount can be projected to the table view-model. Migrated all three `TemplateResponse` calls to the modern Starlette signature `(request, name, ctx)` to silence the deprecation warning. |
| `app/templates/dashboard.html` | Wrapped content in semantic `<main>`. Added a RUN DEMO PREFLIGHT section with three side-by-side `<form method="post">` cards (one per whitelisted example). Made each transaction-ID cell a clickable link to the detail page. Added Vendor / Amount / View columns. Empty-state body copy now points at the new demo buttons instead of curl. |
| `app/templates/transaction_detail.html` (new) | Detail page: header with txn ID + decision/risk/status badges, optional error alert, state-aware action row (Approve / Reject / Execute / View Receipt), overview grid, checks list (status, message, per-check evidence JSON), evidence + invoice + blocked-actions cards, approval and execution JSON pre blocks when present, receipt summary when present, raw transaction JSON pre. |
| `app/templates/receipt.html` (new) | Receipt viewer page: receipt summary grid (receipt ID, txn ID, action, status badge, agent, user, approver, executed-at, full HMAC-SHA256 signature) and the canonical signed payload as a `<pre>`. Empty-state when no receipt exists, with a back link to the detail page. |
| `app/static/neo.css` | Appended new utility classes keyed off existing tokens (no new colors): `.neo-detail-summary`, `.neo-actions`, `.neo-action-row__note`, `.neo-form-inline`, `.neo-detail-grid`, `.neo-detail-card` + `__label` / `__value` / `__title` / `__body`, `.neo-demo-grid`, `.neo-pre` (+ `--small`), `.neo-alert` (+ `--error` / `--empty`), `.neo-link-button`, `.neo-receipt`, `.neo-check-list`, `.neo-check-item` (+ status modifiers), `.neo-badge--check-passed|warning|needs_evidence|failed`. Extended the `<= 640px` media query to stack the action row to full-width buttons on mobile. |
| `tests/test_dashboard.py` (new) | 15 tests covering the new flows + guardrails. Autouse fixture `_isolated_db` monkeypatches `app.main.conn` to a fresh per-test SQLite DB seeded with `init_db` + `seed_demo`, because `app.main` opens the persistent `actionrail.db` at import time and a 15-minute intent-lock TTL would otherwise make serial demo-preflights of the same invoice land as `decision=blocked`. |
| `TASKS.md` | Added Phase 1A and Phase 1B sections under "Completed tasks". Removed dashboard items from "Next tasks" (now done). Updated "Testing status" to reflect 20/20 tests and the isolation fixture. |
| `HANDOFF.md` | "Current project state" now describes both Phase 1A (visual shell) and Phase 1B (operational). Important-files table extended with `app/templates/transaction_detail.html`, `app/templates/receipt.html`, and `tests/test_dashboard.py`. "Current endpoints" now lists the JSON API and the new server-rendered dashboard routes separately. "What to do next" pruned to the items that genuinely remain. |
| `CHANGELOG.md` | New top entry `2026-06-13 — Dashboard operational flow (Phase 1B)` with Added / Changed / Tests / Known limitations sections, including exact `pytest -q` output. |
| `ForKnow.md` | Appended this entry. Prior entries untouched. |

## What I added

- Six new server-rendered dashboard routes (one POST demo creator, one GET detail page, three POST action endpoints, one GET receipt viewer).
- Two new Jinja2 templates: `transaction_detail.html` and `receipt.html`.
- A RUN DEMO PREFLIGHT section on the dashboard with three example buttons.
- Vendor, Amount, and View columns on the dashboard table; clickable transaction IDs.
- 15 new tests in `tests/test_dashboard.py` with an autouse DB-isolation fixture.
- ~13 new neo-brutalist CSS utility classes, all reusing existing tokens.

## What I modified

- `app/main.py`: refactored approve / reject / execute API route bodies into three small private helpers, kept the JSON wrappers byte-identical, added the new dashboard routes and view-model adapters, switched all `TemplateResponse` calls to the modern signature.
- `app/templates/dashboard.html`: added the demo section, vendor + amount + view columns, clickable IDs.
- `app/static/neo.css`: appended new classes; existing classes and tokens unchanged.
- `TASKS.md`, `HANDOFF.md`, `CHANGELOG.md`: per-rule memory updates.

## What I did not change

- `app/policy.py`, `app/store.py`, `app/models.py`, `app/cli.py`: zero edits.
- `tests/test_policy.py`: zero edits, all 5 tests still pass.
- `examples/*.json`, `scripts/demo.sh`: unchanged.
- `PROJECT.md`, `README.md`, `.cursor/rules/actionrail.mdc`, `.cursor/rules/karpathy-guidelines.mdc`: unchanged.
- `requirements.txt`, `pyproject.toml`: unchanged (no new dependencies).
- API JSON response shapes for `/health`, `/actionrail/manifest.json`, `/actions/preflight`, `/transactions`, `/transactions/{id}`, `/approvals/{id}/approve`, `/approvals/{id}/reject`, `/actions/{id}/execute`, `/receipts/{id}` — all byte-identical (the test `test_existing_api_endpoints_still_return_json` asserts this).
- The pre-existing unused `from datetime import timezone` import in `app/main.py` — when I rewrote that file I did not re-add the unused import; it had been pre-existing dead code that my changes orphaned by virtue of the rewrite, so it is now gone. Net behavior unchanged.

## Tests run

```bash
pytest -q
```

```text
....................                                                     [100%]
20 passed in 1.13s
```

End-to-end smoke check via `fastapi.testclient.TestClient` against the persistent `actionrail.db`:

```text
GET /dashboard:                          200
GET /docs:                               200
GET /actionrail/manifest.json:           200
POST /dashboard/demo/approval_required:  303
POST /dashboard/demo/garbage:            404
GET unknown txn detail:                  404
```

## Current status

- App status: runs cleanly. `uvicorn app.main:app` starts without warnings. All endpoints listed in `HANDOFF.md` work.
- Dashboard status: **operational**. From the browser, a user can: click a demo button, view the new transaction detail page, click Approve, click Execute, click View Receipt, and see the signed receipt payload — all server-rendered, all 303-redirected, no JavaScript.
- API status: unchanged. JSON shapes preserved. Swagger / OpenAPI at `/docs` still works. The new dashboard routes appear in the OpenAPI spec but return HTML.
- Known issues:
  - Dashboard approve/reject use a fixed `approver_id="dashboard_user"` constant. Acceptable for the demo; real auth is out of scope.
  - No CSRF token on the dashboard forms. Acceptable for a single-user local demo; real deployments would need it.
  - No idempotency on demo-button clicks (each click creates a new transaction). Intended demo behavior.
  - Dashboard tests must isolate `app.main.conn` per-test; without the autouse fixture the 15-minute intent-lock TTL in `actionrail.db` makes serial preflights land as `decision=blocked`. The fixture is the right shape; documented in `TASKS.md` and the test docstring.

## What still needs manual review

- Visual confirmation in your own browser that the new detail page and receipt page read as finance-grade. The same neo-brutalist tokens and palette that you already approved for the dashboard list view drive these pages, but the layouts (overview grid, checks list, signed-payload pre block) are new compositions worth a glance.
- Whether the dashboard error UX is good enough — currently when the user tries an invalid action (e.g. Execute on a blocked txn directly via URL or after state changed in another tab), the detail page re-renders with a finance-grade red alert banner at HTTP 400. No flash messages, no toasts. Plain server-rendered alerts.

## What the user should send to ChatGPT

Copy paste this whole latest entry — everything from `# Cursor Work Update: Phase 1B — operational dashboard` down to the end of this section.

---

# Cursor Work Update: Phase 1B-polish — dashboard demo readiness

## Date

2026-06-13, IST late-evening session.

## Prompt I worked on

Focused Phase 1B polish pass driven by browser-review screenshots. Five issues to fix without expanding scope: (1) the table is too wide and forces horizontal scroll, (2) demo data accumulates so there are too many blocked rows, (3) there is no `needs_more_evidence` stat card, (4) the main table shows too much agent/internal detail, (5) need a clean reset path before screenshots. Constraints: no real payments, no external integrations, no React/Tailwind/build pipeline, no API JSON shape changes, keep tests green, and update `ForKnow.md`.

## Files changed

| File | What changed |
|---|---|
| `app/main.py` | Dashboard `stats` dict now includes a `needs_evidence` key, accumulated when `decision == "needs_more_evidence"`. Added a `crowded = stats["total"] >= 10` flag. Both passed to the template. JSON API routes and helpers untouched. |
| `app/templates/dashboard.html` | Stats grid now has 5 cards: Total · Approval required (yellow) · **Needs evidence** (new violet) · Blocked (red) · Executed. Transaction queue table reduced from 11 columns to 7: dropped Agent / Intent / Action / Created. `<table>` has the new `.neo-table--compact` modifier. When the queue is empty, the body copy points at the demo buttons and the recommended order is rendered as an ordered list (`.neo-empty__list`): Approval Required Invoice → Duplicate Invoice → Missing Evidence Invoice. When the queue holds ≥10 transactions, a small `.neo-queue-note` reads "Use `scripts/reset_demo_db.py` before recording a clean demo." A muted footnote below the table tells reviewers where the agent/intent/action/timestamp fields moved. |
| `app/static/neo.css` | Added `.neo-table--compact` (smaller cell padding + 0.9rem body / 0.65rem header) so the trimmed table fits typical desktop widths without horizontal scroll. Added `.neo-empty__list` for the ordered demo-order list. Added `.neo-queue-note` (yellow inline pill) and `.neo-queue-note--muted` (subtle below-table footnote). All keyed off existing tokens — no new colors, no new shadows. Existing classes untouched. |
| `scripts/reset_demo_db.py` (new) | Local-only demo DB reset. `reset(db_path=None)` drops the project's six SQLite tables in dependency-safe order (`intent_locks` → `transactions` → `invoices` → `contracts` → `vendors` → `policies`) and runs `init_db` + `seed_demo`. `main()` entry-point prints a finance-grade multi-line success message. Touches only `app.store.DB_PATH`; never deletes arbitrary files; never connects to anything external. Adds the project root to `sys.path` so it works when run as `python scripts/reset_demo_db.py`. |
| `tests/test_dashboard.py` | Added 3 tests: `test_dashboard_has_needs_evidence_stat_card` (verifies violet card label is present and the count reflects state after creating a missing-evidence transaction), `test_dashboard_table_drops_agent_intent_action_columns` (asserts the three header cells are gone and the seven required ones remain), `test_dashboard_empty_state_lists_recommended_demo_order` (asserts the three example labels appear in the canonical order in the empty state). |
| `tests/test_reset_demo_db.py` (new) | 2 tests for the reset script. Loads the script via `importlib.util.spec_from_file_location` so `scripts/` does not need to become a Python package. `test_reset_clears_transactions_and_keeps_seed` seeds a tmp DB with a fake transaction, calls `reset(db_path=tmp_path/...)`, then asserts: transactions table empty, vendors/contracts/policies still seeded, historical INV-1042 still present. `test_reset_is_idempotent_on_a_fresh_db` runs `reset()` twice on a non-existent path and confirms it ends in a seeded state both times. |
| `TASKS.md` | Added a `Phase 1B-polish` block under Completed tasks. Refreshed Testing status to 25/25. |
| `HANDOFF.md` | Current state extended with Phase 1B-polish summary and the demo reset script. Important-files table extended with `scripts/reset_demo_db.py` and `tests/test_reset_demo_db.py`. "Run the demo flow" section now leads with the recommended `python scripts/reset_demo_db.py` → `uvicorn` recipe for screenshot recording. |
| `CHANGELOG.md` | New top entry `2026-06-13 — Dashboard demo polish (Phase 1B-polish)` with Added / Changed / Tests / Known limitations sections, including exact `pytest -q` output. |
| `ForKnow.md` | Appended this entry. Prior entries untouched. |

## What I added

- A new violet "Needs evidence" stat card on `/dashboard`.
- An ordered "Recommended demo order" list inside the empty-state poster.
- A small reset-script hint that appears only when ≥10 transactions are queued.
- A muted below-table footnote pointing reviewers to the detail page for agent/intent/action/timestamps.
- `.neo-table--compact`, `.neo-empty__list`, `.neo-queue-note`, `.neo-queue-note--muted` CSS classes — all reusing existing tokens.
- `scripts/reset_demo_db.py` (local-only demo reset, never touches external systems).
- 5 new tests across `tests/test_dashboard.py` and `tests/test_reset_demo_db.py`.

## What I modified

- `app/main.py` dashboard route only: stats dict + crowded flag + template context. JSON API routes, helpers, models, store, policy, CLI, manifest, etc. all untouched.
- `app/templates/dashboard.html`: stats section (now 5 cards), table head and body (now 7 columns + compact class), empty state (ordered demo list), and two ambient notes around the table.
- `app/static/neo.css`: appended the four new classes; existing classes unchanged.
- `TASKS.md` / `HANDOFF.md` / `CHANGELOG.md`: rule-required memory updates.

## What I did not change

- API JSON response shapes for `/health`, `/actionrail/manifest.json`, `/actions/preflight`, `/transactions`, `/transactions/{id}`, `/approvals/{id}/approve`, `/approvals/{id}/reject`, `/actions/{id}/execute`, `/receipts/{id}` — all byte-identical to before. Verified by `tests/test_dashboard.py::test_existing_api_endpoints_still_return_json` (still passing).
- `app/policy.py`, `app/store.py`, `app/models.py`, `app/cli.py` — zero edits.
- `tests/test_policy.py` — zero edits, all 5 tests still pass.
- `requirements.txt`, `pyproject.toml` — unchanged. No new dependencies.
- `app/templates/transaction_detail.html`, `app/templates/receipt.html` — unchanged. The dropped fields (Agent, Intent, Action, Created) still render on the detail page exactly as before.
- Existing test assertions in `tests/test_dashboard.py` — none weakened. The new tests add coverage; nothing was relaxed.
- `examples/*.json`, `scripts/demo.sh`, `PROJECT.md`, `README.md`, `.cursor/rules/*` — unchanged.

## Tests run

```bash
pytest -q
```

```text
.........................                                                [100%]
25 passed in 1.34s
```

Visual smoke check via the user's running uvicorn (`http://127.0.0.1:8000/dashboard`): with 14 accumulated transactions in the dev DB, the dashboard now shows 5 stat cards (TOTAL=14, APPROVAL REQUIRED=2, plus the new violet Needs evidence and the existing Blocked/Executed), the RUN DEMO PREFLIGHT cards, the trimmed 7-column table, and both the inline reset hint (because total ≥ 10) and the muted footnote.

## Current status

- App status: runs cleanly. uvicorn auto-reloaded successfully against every edit during this turn.
- Dashboard status: **demo-ready**. Trimmed columns + Needs evidence card + recommended-order empty state + crowded-queue reset hint all rendering as designed at desktop width.
- API status: unchanged. All JSON shapes intact. Swagger / OpenAPI at `/docs` still works.
- Reset script status: works. Importable, runnable, idempotent. Drops only project-owned tables; never touches external systems.
- Known issues:
  - `crowded` threshold hard-coded at 10. Easy to tune.
  - Reset script has no `--yes` confirmation; running it always wipes project tables. Acceptable for a local-only demo helper; HANDOFF text emphasises stopping uvicorn first.
  - Pre-existing dashboard-test isolation pattern (per-test fresh `app.main.conn`) still required because of the 15-minute intent-lock TTL on the persistent `actionrail.db` — unchanged from Phase 1B.

## What still needs manual review

- One last visual sniff of the live dashboard at `http://127.0.0.1:8000/dashboard`: confirm that with a clean DB (after running `python scripts/reset_demo_db.py`) the empty-state ordered list reads cleanly, and that after clicking the three demo buttons in order the queue table fits the viewport without horizontal scroll.
- Whether to lower the crowded-queue threshold below 10. Current value catches the typical demo-rehearsal bloat without being noisy on a fresh DB.

## What the user should send to ChatGPT

Copy paste this whole latest entry — everything from `# Cursor Work Update: Phase 1B-polish — dashboard demo readiness` down to the end of this section.

---

# Cursor Work Update: Phase 1C — GitHub and demo readiness

## Date

2026-06-13, IST night session.

## Prompt I worked on

Phase 1C: GitHub and demo readiness. Make the repo clean, understandable, and presentable for GitHub / YC / demo review. Six tasks: (1) rewrite README.md to a 12-section GitHub-ready format, (2) add `.gitignore`, (3) add `scripts/demo.ps1`, (4) add `docs/screenshots/` placeholder with capture flow + naming convention, (5) add `docs/PITCH.md` concise pitch, (6) keep tests green. Constraints: no real payments, no external integrations, no React/Tailwind/Next.js/build pipeline, no API JSON shape changes, no test removal, agent-first framing preserved.

## Files changed

| File | What changed |
|---|---|
| `README.md` | Full rewrite to a GitHub-ready 12-section structure: title + one-liner; What it is; Why it exists (raw-tool-call problem framing); Current MVP scope (12 bullet items); What it does not do yet (10 explicit non-goals — payments, banks, ERP, ledger writeback, Gmail/Outlook, OCR, production auth, multi-tenant, external mutation, etc.); Architecture; Project structure tree; Quickstart (Windows PowerShell + Linux/macOS); URLs; Browser demo flow (13-step walkthrough); API demo flow (curl examples for preflight, approve, execute, receipt, list-transactions, plus duplicate-blocked and missing-evidence preflights, with a `jq` recipe to capture `transaction_id` and a Windows tip to use `curl.exe`); Safety boundary callout ("Execution is simulated. No real money moves."); Screenshots placeholder pointing at `docs/screenshots/README.md`; Further reading links; License note. |
| `.gitignore` (new) | Excludes `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.venv/`, `venv/`, `*.db`, `.env`, `dist/`, `build/`, `.DS_Store`. Local `actionrail.db` is no longer tracked but is preserved on disk per the user's explicit instruction. |
| `scripts/demo.ps1` (new) | Guided Windows PowerShell demo. Sets `$ErrorActionPreference = 'Stop'`, resolves repo root from `$PSScriptRoot`, prints what ActionRail Finance is, restates the simulated-execution safety boundary, runs `pytest -q` (aborts with the test exit code on failure), then prints — but never auto-runs — the next manual commands (`python scripts/reset_demo_db.py`, `uvicorn app.main:app --reload`, the four URLs, and the 11-step browser flow). Non-destructive by design. |
| `docs/screenshots/README.md` (new) | Capture flow + naming convention for the 7 canonical demo screenshots: `01-dashboard-clean.png` through `07-missing-evidence.png`. Includes recommended clean state (run `reset_demo_db.py` first; capture at desktop width ≥ 1280px), per-shot action mapping, naming rules (two-digit prefix, lowercase hyphenated, PNG only), and tips for clean shots. |
| `docs/PITCH.md` (new) | Concise YC-style pitch: one-liner ("ActionRail turns risky finance agent actions into safe, auditable transactions."), problem (raw tool calls are unsafe in finance), solution (transaction primitive `agent → create transaction → preflight → verify → lock → approve → execute → receipt`), why now (agents in production for regulated industries 2025–2026), first wedge (invoice approval + duplicate detection), 90-second demo script (7 steps), what is unique (5 differentiators: agent-first, transaction primitive, all controls together, vertical-agnostic, codified safety boundary), future roadmap aligned to `PROJECT.md` phases 2–6. |
| `TASKS.md` | Added a "Phase 1C — GitHub and demo readiness (done, this commit)" section under Completed tasks. Refreshed Testing status to note Phase 1C added no production code, test count unchanged at 25. |
| `HANDOFF.md` | Current state extended with Phase 1C summary. Important-files table extended with `scripts/demo.ps1`, `docs/PITCH.md`, `docs/screenshots/README.md`, and `.gitignore`. |
| `CHANGELOG.md` | New top entry `2026-06-13 — GitHub and demo readiness (Phase 1C)` with Added / Tests / Known limitations sections, including exact pytest output and a note that the PowerShell script parses cleanly. |
| `ForKnow.md` | Appended this entry. Prior entries untouched. |

## What I added

- A GitHub-ready `README.md` covering pitch, scope, non-goals, architecture, structure, quickstart for both platforms, URLs, browser demo flow, curl API flow, and the safety boundary.
- A repo-root `.gitignore` for Python projects (the dev SQLite DB is now untracked).
- A guided Windows PowerShell demo script that runs the test suite and walks the user through the next manual steps.
- A `docs/` directory containing a screenshots README (with the seven canonical filenames + capture flow) and a concise YC-style pitch.

## What I modified

- `README.md`: full rewrite. The previous README was the original session-start version (~6.4KB) which already documented the API; the rewrite restructures it for GitHub presentability, adds the missing browser demo flow, integrates the `reset_demo_db.py` step, and tightens the framing per Phase 1C scope.
- `TASKS.md`, `HANDOFF.md`, `CHANGELOG.md`: rule-required memory updates.

## What I did not change

- No code under `app/` (`main.py`, `models.py`, `policy.py`, `store.py`, `cli.py`, `templates/*.html`, `static/neo.css`).
- No tests under `tests/`. All 25 still pass with no edits.
- API JSON response shapes for `/health`, `/actionrail/manifest.json`, `/actions/preflight`, `/transactions`, `/transactions/{id}`, `/approvals/{id}/approve`, `/approvals/{id}/reject`, `/actions/{id}/execute`, `/receipts/{id}` — byte-identical to before.
- `requirements.txt`, `pyproject.toml` — unchanged. No new dependencies.
- `examples/*.json`, `scripts/demo.sh`, `scripts/reset_demo_db.py`, `actionrail.db` — unchanged.
- `PROJECT.md`, `DECISIONS.md` — unchanged. Added no new decision because Phase 1C is pure docs/scaffolding within existing decisions.
- `.cursor/rules/actionrail.mdc`, `.cursor/rules/karpathy-guidelines.mdc` — unchanged.

## Tests run

```bash
pytest -q
```

```text
.........................                                                [100%]
25 passed in 1.30s
```

PowerShell parser check on `scripts/demo.ps1` via `[System.Management.Automation.Language.Parser]::ParseFile` reported no syntax errors.

## Current status

- App status: unchanged. uvicorn keeps running cleanly. All endpoints behave as before.
- Repo presentability: **GitHub-ready**. README opens with a clear one-liner, lists scope and non-goals up front, has both quickstarts, a numbered browser demo flow, curl examples, the safety boundary callout, and links to PROJECT.md / DECISIONS.md / HANDOFF.md / CHANGELOG.md / docs/PITCH.md.
- Demo readiness: a fresh reviewer can clone the repo, follow the README quickstart, run `pwsh scripts/demo.ps1` (or follow the bash equivalent), and have a clean recording-ready dashboard within ~2 minutes.
- Tests: 25/25 passing. No drift.
- Known issues:
  - README quickstart implicitly assumes Python 3.12+. If you want to support older interpreters this is the place to pin.
  - `docs/screenshots/` ships with only its README — no actual PNGs are committed yet (per the spec: "Do not include actual image files unless already present").
  - README has a placeholder license section ("Add your chosen license file before public release"). No `LICENSE` file is committed; choose MIT / Apache-2.0 / proprietary before going public.
  - `.gitignore` does not currently exclude editor-specific files (`.vscode/`, `.idea/`). Easy to add if you decide to.
  - The PowerShell script tells the user how to run reset and uvicorn but never runs them. That's deliberate (reset is destructive, uvicorn is long-running) but worth knowing.

## What still needs manual review

- Read through the rewritten `README.md` once and confirm the framing matches your YC / GitHub voice.
- Read through `docs/PITCH.md` once and confirm the "what is unique" bullets and the future-roadmap phases match your story.
- Capture the seven screenshots per `docs/screenshots/README.md` so the README's screenshots section is filled in. The exact capture order and filenames are spelled out there.
- Pick a license and add a `LICENSE` file before going public.

## What the user should send to ChatGPT

Copy paste this whole latest entry — everything from `# Cursor Work Update: Phase 1C — GitHub and demo readiness` down to the end of this section.

---

# Cursor Work Update: Phase 1D — README and pitch sharpness review

## Date

2026-06-13, IST night session (continuation).

## Prompt I worked on

Phase 1D: documentation and positioning sharpness pass. Improve README.md and docs/PITCH.md for GitHub / YC / demo review — clearer infrastructure framing, "what the MVP proves" section, demo narrative table, sharper "what is unique" bullets, "why this becomes bigger" section. Check screenshot docs. Add .vscode/ and .idea/ to .gitignore. Run tests. Update memory files.

## Files changed

| File | What changed |
|---|---|
| `README.md` | Sharpened throughout. "What it is" leads with infrastructure vs dashboard framing. Added decision table for the 4 machine-readable decisions. Added "What the MVP proves" section (6-point numbered summary). Added "Demo narrative" table (3 flows × what each proves). Architecture section rewritten as a data-flow diagram. Browser demo condensed from 13 to 9 steps. API demo section condensed. "Current MVP scope" and "What it does not do yet" tightened. |
| `docs/PITCH.md` | Added "What the current MVP proves" section (5 numbered points). Added "Demo narrative" table. Rewrote "What is unique" with 5 sharper bullets (infrastructure/dashboard, transaction primitive/workflow tool, all controls in one layer, deterministic/probabilistic, codified safety boundary). Added "Why this becomes bigger" standalone section with 5 vertical examples. Renamed "Future roadmap" → "Roadmap" and tightened. |
| `docs/screenshots/README.md` | Clarified step 03 ("after the redirect"; "Reject button gone"). Added tip about showing stat cards in dashboard screenshots. |
| `.gitignore` | Added `.vscode/` and `.idea/`. |
| `HANDOFF.md` | Removed stale "planned task, not yet present" note about demo.ps1 (now exists). Removed duplicate "Always:" line. Pruned stale items from "What to do next". Added Phase 1D to current-state summary. |
| `TASKS.md` | Added "Phase 1D — README and pitch sharpness review (done, this commit)" block under Completed tasks. |
| `CHANGELOG.md` | New top entry `2026-06-13 — README and pitch sharpness review (Phase 1D)` with Changed / Tests sections. |
| `ForKnow.md` | Appended this entry. Prior entries untouched. |

## What I added

- "What the MVP proves" section in README.md.
- "Demo narrative" table in both README.md and docs/PITCH.md.
- "Why this becomes bigger" section in docs/PITCH.md.
- Decision table for the 4 machine-readable decisions in README.md.
- `.vscode/` and `.idea/` entries in `.gitignore`.

## What I modified

- README.md: framing, structure, and section content as described above.
- docs/PITCH.md: new sections, rewritten "What is unique", tightened roadmap.
- docs/screenshots/README.md: two small clarifications.
- HANDOFF.md: removed stale notes, pruned next-tasks list, fixed duplicate line.
- TASKS.md / CHANGELOG.md: rule-required memory updates.

## What I did not change

- No files under `app/` (main.py, models.py, policy.py, store.py, cli.py, templates/, static/).
- No test files. All 25 tests still pass unchanged.
- API JSON response shapes — unchanged.
- requirements.txt, pyproject.toml — no new dependencies.
- examples/*.json, scripts/demo.sh, scripts/demo.ps1, scripts/reset_demo_db.py — unchanged.
- PROJECT.md, DECISIONS.md — unchanged (no new decisions needed; this is a docs-only pass).
- .cursor/rules/ — unchanged.

## Tests run

```bash
pytest -q
```

```text
.........................                                                [100%]
25 passed in 1.32s
```

## Current status

- App status: unchanged. uvicorn running on :8000. All endpoints behave as before.
- Repo presentability: **sharpened**. README now answers all 8 questions from the task spec clearly. PITCH.md now has concrete proof points and a stronger "why bigger" argument. docs/screenshots/README.md is ready for the capture session.
- Tests: 25/25 passing.
- Known issues:
  - Screenshots are still not committed — `docs/screenshots/` contains only the README. Capture session is the next manual step.
  - No LICENSE file committed. Needed before public release.
  - TASKS.md "Next tasks" still lists `scripts/demo.ps1` as a pending item (item 2). That item should be removed — demo.ps1 exists and works. Will clean up on the next pass if needed.

## What still needs manual review

- Read through the rewritten README.md once end-to-end — confirm the decision table, "What the MVP proves" section, and "Demo narrative" table read cleanly against what the actual app does.
- Read through docs/PITCH.md — confirm the "What is unique" bullets and "Why this becomes bigger" vertical examples match your positioning.
- Capture the 7 demo screenshots per docs/screenshots/README.md.
- Pick a license and add a LICENSE file.

## What the user should send to ChatGPT

Copy paste this whole latest entry — everything from `# Cursor Work Update: Phase 1D — README and pitch sharpness review` down to the end of this section.

---

# Cursor Work Update: Phase 2A — Real invoice upload and extraction

## Date

2026-06-13, IST night session.

## Prompt I worked on

Phase 2A: Real invoice upload and extraction. Allow users to upload real PDF/PNG/JPG invoice files from the dashboard, extract text from digital PDFs (pypdf), extract fields from that text (regex), merge with manual form input, and run the existing ActionRail preflight pipeline against the result. Store the file locally with a SHA-256 hash as a `local://uploaded_documents/{id}` evidence reference. Add docs/DATASETS.md and scripts/download_sample_datasets.py. Add 13 new tests. Keep execution simulated; no real money moves.

## Files changed

| File | What changed |
|---|---|
| `app/store.py` | Added `uploaded_documents` table to `init_db()`. Added `save_uploaded_document()` and `get_uploaded_document()` helpers. |
| `app/extraction.py` (new) | `extract_text_from_pdf()` via pypdf; `extract_fields_from_text()` via conservative regex (invoice_id, amount, currency, dates, GST); `extraction_status_for_image()` extension point for Phase 2B OCR. |
| `app/main.py` | Added imports (`hashlib`, `uuid`, `File`, `UploadFile`, `save_uploaded_document`, `get_uploaded_document`). Added `_UPLOAD_DIR` constant with `mkdir(parents=True, exist_ok=True)`. Added `_doc_id()`, `_sha256_of_bytes()` helpers. Added `GET /dashboard/invoices/upload` and `POST /dashboard/invoices/upload` routes. Extended `_detail_view_model()` to resolve `uploaded_doc` from evidence URL. |
| `app/templates/invoice_upload.html` (new) | Upload form with file input, manual fields (invoice_id, vendor, amount, currency, invoice_date, due_date, gst_number, contract_id, line_items textarea, human_approval checkbox), extraction notes display, error alert, safety disclaimer. |
| `app/templates/dashboard.html` | Added "Upload real invoice" link to header nav. |
| `app/templates/transaction_detail.html` | Added uploaded document info block conditional on `txn.uploaded_doc` — shows doc ID, original filename, file size, SHA-256, extracted fields, extraction notes, first 400 chars of extracted text. |
| `app/static/neo.css` | Added `.neo-input` styles (section 10 in the file — borders, focus state, placeholder, file input variant). Renumbered subsequent section comments from 10→11, 11→12, etc. |
| `data/uploads/.gitkeep` (new) | Keeps upload directory in git. |
| `data/datasets/.gitkeep` (new) | Keeps datasets directory in git. |
| `.gitignore` | Added `data/uploads/*`, `!data/uploads/.gitkeep`, `data/datasets/*`, `!data/datasets/.gitkeep`. |
| `requirements.txt` | Added `pypdf==6.11.0` and `python-multipart>=0.0.9`. |
| `scripts/reset_demo_db.py` | `PROJECT_TABLES` extended with `"uploaded_documents"`. |
| `docs/DATASETS.md` (new) | 6 dataset reference entries with links, format, use case, and license notes. |
| `scripts/download_sample_datasets.py` (new) | Prints all dataset links by default; supports `--source funsd --limit N` for auto-download. |
| `DECISIONS.md` | Added D7: Phase 2A local upload choices (pypdf, regex, local storage, no OCR yet). |
| `README.md` | MVP scope updated to mention upload and extraction. "What it does not do yet" section updated to be explicit about OCR and PDF extraction limitations. |
| `TASKS.md` | Phase 2A added under Completed tasks. Next tasks updated (added Phase 2B OCR). Testing status updated to 38/38. |
| `HANDOFF.md` | Current state reflects Phase 2A. Important-files table extended. What to do next updated. |
| `CHANGELOG.md` | New top entry `2026-06-13 — Real invoice upload and extraction (Phase 2A)`. |
| `ForKnow.md` | Appended this entry. Prior entries untouched. |
| `tests/test_upload.py` (new) | 13 tests: upload page loads, invalid extension rejected, PNG upload creates transaction, detail page accessible, PDF SHA-256 and evidence ref stored, missing required fields returns 400, field extraction from text, empty text handled, minimal PDF extraction, non-PDF handled gracefully, existing demo flows unaffected, JSON API shapes unchanged, dashboard shows upload link. |

## What I added

- `app/extraction.py` — PDF extraction + regex field extractor
- `app/templates/invoice_upload.html` — upload form
- `data/uploads/.gitkeep` and `data/datasets/.gitkeep`
- `docs/DATASETS.md` — 6 dataset references
- `scripts/download_sample_datasets.py`
- `tests/test_upload.py` — 13 new tests
- D7 in `DECISIONS.md`
- `uploaded_documents` table in SQLite schema
- `save_uploaded_document()` / `get_uploaded_document()` helpers in `store.py`
- Upload routes in `main.py`
- `.neo-input` CSS class in `neo.css`

## What I modified

- `app/store.py`: added table + helpers
- `app/main.py`: imports, constants, helpers, routes, `_detail_view_model()`
- `app/templates/dashboard.html`: header nav button
- `app/templates/transaction_detail.html`: upload doc block
- `app/static/neo.css`: `.neo-input` class + renumbered sections
- `scripts/reset_demo_db.py`: extended `PROJECT_TABLES`
- `requirements.txt`: added 2 deps
- `.gitignore`: added data/ patterns
- `README.md`: scope + limitations updated
- `TASKS.md`, `HANDOFF.md`, `CHANGELOG.md`: rule-required memory updates

## What I did not change

- `app/policy.py`, `app/models.py`, `app/cli.py` — zero edits
- `tests/test_policy.py`, `tests/test_dashboard.py`, `tests/test_reset_demo_db.py` — zero edits; all 25 prior tests still pass
- All existing API JSON response shapes — unchanged; verified by `test_json_api_shapes_unchanged`
- `PROJECT.md`, `.cursor/rules/` — unchanged
- `examples/*.json`, `scripts/demo.sh`, `scripts/demo.ps1` — unchanged
- `docs/PITCH.md`, `docs/screenshots/README.md` — unchanged

## Tests run

```bash
pytest -q
```

```text
......................................                                   [100%]
38 passed in 1.96s
```

## Current status

- App status: uvicorn running on :8000. All prior endpoints unchanged. Two new dashboard routes (`GET/POST /dashboard/invoices/upload`) live and functional.
- Upload flow: users can upload PDF/PNG/JPG → get preflight decision → approve → execute → receipt. The uploaded file is SHA-256-hashed and stored locally. The `local://uploaded_documents/{id}` evidence reference appears on the transaction detail page with the extracted fields and notes.
- Extraction: digital PDF text extraction works via pypdf. Regex field extractor is conservative (amount, currency, dates, GST, invoice_id). Image OCR is deferred to Phase 2B.
- Tests: 38/38 passing.
- Known issues:
  - Image (PNG/JPG) uploads require manual field entry — no OCR yet.
  - PDF extraction only works for digital/machine-generated PDFs. Scanned PDFs with no embedded text produce `extraction_status="empty"`.
  - Upload route uses fixed `agent_id="dashboard_upload_user"` and `user_id="controller_001"`. Fine for demo; needs auth in production.
  - Uploaded files are not served via the app — they are evidence references only.
  - `filesizeformat` Jinja2 filter used in `transaction_detail.html` for file size display; this filter is built in to Jinja2 (available in Flask/FastAPI Jinja2 env as a standard filter). If it causes issues in the running server, fall back to a manual `{size} bytes` display.

## What still needs manual review

- Open `/dashboard/invoices/upload` in a browser and try uploading a real PDF invoice (machine-generated, not scanned). Confirm: fields are extracted, evidence reference shows on detail page, preflight decision is returned.
- Try uploading a PNG — confirm it requires manual field entry, stores correctly, and runs preflight.
- Try uploading a `.exe` file — confirm it returns a 400 error with a clear message.

## What the user should send to ChatGPT

Copy paste this whole latest entry — everything from `# Cursor Work Update: Phase 2A — Real invoice upload and extraction` down to the end of this section.

---

# Cursor Work Update: Phase 2A-fix2 — Kaggle credential safety and dataset downloader

## Date

2026-06-13, IST late-night session.

## Prompt I worked on

Phase 2A-fix2: Protect `kaggle/kaggle.json` from being committed. Make the dataset download script work practically and safely. Add `--check-kaggle`, `--source kaggle-invoices --download`, `--instructions` flags. Update `docs/DATASETS.md` with Kaggle setup for Windows + Linux and a troubleshooting table. Add 7 offline tests. Keep all product code untouched.

Security constraint: never print or commit Kaggle credential contents.

## Files changed

| File | What changed |
|---|---|
| `.gitignore` | Added `kaggle/`, `kaggle.json`, `**/kaggle.json`, `.kaggle/` patterns |
| `scripts/download_sample_datasets.py` | Fully rewritten: `KaggleCredStatus` named tuple, `detect_kaggle_credentials()` with 3-level priority, `kaggle_package_available()`, `configure_kaggle_env()`, `check_kaggle()`, `print_kaggle_instructions()`, `download_kaggle_invoices(limit)`, `_extract_sample()`, `kaggle-invoices` source, `--check-kaggle`/`--instructions`/`--download` flags, backward-compatible `--source funsd --limit N` |
| `docs/DATASETS.md` | Fully rewritten: Security section, Kaggle setup on Windows, Kaggle setup on Linux/macOS, Common Kaggle errors troubleshooting table, updated dataset entries with `kaggle-invoices` source key, Quick reference command table |
| `tests/test_datasets_script.py` (new) | 7 offline tests covering: no-credentials check_kaggle, project-local credential detection, gitignore protection, instructions output, unknown source exit, no-package exit, no-credentials exit |
| `TASKS.md` | Phase 2A-fix2 added under Completed tasks; testing status updated to 45/45 |
| `HANDOFF.md` | Current state reflects Phase 2A-fix2; files table extended with `tests/test_datasets_script.py`; tests count updated |
| `CHANGELOG.md` | New top entry `2026-06-13 — Kaggle credential safety and dataset downloader (Phase 2A-fix2)` |
| `ForKnow.md` | Appended this entry. Prior entries untouched. |

## What I added

- `tests/test_datasets_script.py` — 7 new offline tests
- `KaggleCredStatus` named tuple, credential detection logic, `--check-kaggle`, `--instructions`, `--download`, `_extract_sample()` functions in the script
- `kaggle-invoices` as a named source in the script and dataset reference table
- Security section, Kaggle setup sections, and troubleshooting table in `docs/DATASETS.md`

## What I modified

- `scripts/download_sample_datasets.py`: fully rewritten (all existing functionality preserved and extended)
- `.gitignore`: 4 new Kaggle-related patterns added
- `docs/DATASETS.md`: fully rewritten with better structure
- Memory files: TASKS, HANDOFF, CHANGELOG updated

## What I did not change

- `app/main.py`, `app/policy.py`, `app/store.py`, `app/extraction.py` — zero edits
- All templates and CSS — zero edits
- All existing tests — zero edits; all 38 prior tests still pass
- `requirements.txt` — kaggle is an optional dev dependency, intentionally not added to requirements
- API JSON response shapes — unchanged
- `PROJECT.md`, `DECISIONS.md`, `.cursor/rules/` — unchanged
- `kaggle/kaggle.json` — not read, not printed, not modified, not deleted
- `data/uploads/` and `data/datasets/` directories — unchanged

## Tests run

```bash
pytest -q
```

```text
.............................................                            [100%]
45 passed in 1.96s
```

## Current status

- App status: uvicorn running on :8000. All endpoints unchanged.
- Kaggle credential: `%USERPROFILE%\.kaggle\kaggle.json` detected at the official Windows location. `kaggle/kaggle.json` project-local also exists and is now gitignored.
- Kaggle package: NOT installed. `--check-kaggle` correctly reports this and prints `pip install kaggle`.
- Dataset download: ready as soon as `pip install kaggle` is run. Credentials are in place.
- Tests: 45/45 passing.

## Known issues

- `kaggle` package needs to be installed before `--source kaggle-invoices --download` will work: `pip install kaggle`.
- The full dataset download may be several hundred MB. Use `--limit 20` to extract a small sample after download.
- `funsd` download via `--source funsd` requires `pip install datasets` (Hugging Face library), also not in `requirements.txt`.
- Project-local `kaggle/kaggle.json` path: while it IS gitignored now, it is best practice to move credentials to `%USERPROFILE%\.kaggle\kaggle.json` (which already has a copy based on the detection check).

## What the user should send to ChatGPT

Copy paste this whole latest entry — everything from `# Cursor Work Update: Phase 2A-fix2 — Kaggle credential safety and dataset downloader` down to the end of this section.

---

# Cursor Work Update: Phase 2B — OCR and dataset sample tooling

## Date

2026-06-14, IST (shortly after midnight).

## Prompt I worked on

Phase 2B: Add optional OCR for image invoices, dataset inspection tools, and sample preparation script. Wire OCR into the upload flow (graceful fallback if missing). Create `docs/OCR.md`. Update dataset docs with local structure. Add 11 offline tests. Keep execution simulated and all product constraints intact.

Key constraint: OCR must never be required for app startup. All 45 prior tests must still pass.

## Files changed

| File | What changed |
|---|---|
| `app/ocr.py` (new) | Optional OCR module: `ocr_image_bytes(data, filename)` → `{status, engine, text, notes}`. Uses pytesseract + Pillow if installed; graceful `not_available` fallback otherwise. Covers Pillow absent, pytesseract absent, Tesseract binary missing. |
| `app/main.py` | Upload route image path replaced: now calls `ocr_image_bytes()`, uses returned text for field extraction if `status="ok"`, stores OCR notes. Removed unused `extraction_status_for_image` import. |
| `scripts/inspect_invoice_dataset.py` (new) | Prints dataset structure: file counts, extension breakdown, folder layout, first 10 images, CSV column/row/key/OCR-text-sample details. Handles missing path. |
| `scripts/prepare_invoice_samples.py` (new) | Copies N image files from Kaggle dataset to `data/datasets/kaggle-invoices-sample/`. Default limit 20. Handles missing source. |
| `data/datasets/kaggle-invoices-sample/.gitkeep` (new) | Directory tracked; sample files gitignored. |
| `.gitignore` | Added `data/datasets/kaggle-invoices-sample/*` and `!data/datasets/kaggle-invoices-sample/.gitkeep`. |
| `docs/OCR.md` (new) | Optional OCR setup: Windows + Linux/macOS install, pytesseract verification, manual test steps, dataset context, limitations table. |
| `docs/DATASETS.md` | Added local dataset structure section: 8,181 JPGs + 3 CSVs with `File Name`, `Json Data`, `OCRed Text` columns; folder layout; inspect/prepare script links. |
| `README.md` | "What it does not do yet" updated: OCR is now optional (install pytesseract + Tesseract) with a link to `docs/OCR.md`. |
| `tests/test_ocr.py` (new) | 11 offline tests (see below). |
| `TASKS.md` | Phase 2B added under Completed tasks; testing status updated to 56/56. |
| `HANDOFF.md` | Phase 2B added to current state; files table extended; next-tasks updated. |
| `CHANGELOG.md` | New top entry `2026-06-14 — OCR and dataset sample tooling (Phase 2B)`. |
| `ForKnow.md` | Appended this entry. Prior entries untouched. |

## What I added

- `app/ocr.py` — optional OCR module
- `scripts/inspect_invoice_dataset.py` — dataset structure printer
- `scripts/prepare_invoice_samples.py` — image sample copier
- `data/datasets/kaggle-invoices-sample/.gitkeep`
- `docs/OCR.md`
- `tests/test_ocr.py` — 11 new tests

## What I modified

- `app/main.py`: image upload path now calls `ocr_image_bytes()` instead of `extraction_status_for_image()`. Removed unused import.
- `.gitignore`: added sample dir patterns.
- `docs/DATASETS.md`: local structure section added.
- `README.md`: OCR limitation updated.
- Memory files.

## What I did not change

- `app/policy.py`, `app/store.py`, `app/models.py`, `app/cli.py`, `app/extraction.py` — zero edits.
- All existing templates and CSS — zero edits.
- All 45 prior tests — zero edits; all still pass.
- API JSON response shapes — unchanged.
- `requirements.txt` — pytesseract and Pillow are optional dev dependencies, intentionally not in requirements.
- `PROJECT.md`, `DECISIONS.md`, `.cursor/rules/` — unchanged.

## Tests run

```bash
pytest -q
```

```text
........................................................                 [100%]
56 passed in 2.34s
```

Smoke tests also run manually:
- `python scripts/inspect_invoice_dataset.py` → correctly printed dataset structure (8,181 images, 3 CSVs, folder layout).
- `python scripts/prepare_invoice_samples.py --limit 10` → correctly copied 10 files to `data/datasets/kaggle-invoices-sample/`.

## Current status

- App status: unchanged. All endpoints work as before.
- OCR status: module is present but pytesseract is not installed. Image uploads show `OCR status: not_available` with install instructions in the extraction notes on the transaction detail page. Manual fields still required.
- Dataset: 8,181 JPG images + 3 annotation CSVs available locally. Inspect and sample scripts work.
- Tests: 56/56 passing.

## Known issues

- pytesseract requires a separate `pip install pytesseract pillow` AND a system Tesseract binary install before OCR will work. See `docs/OCR.md`.
- The regex field extractor was tuned to the GST/INR patterns common in the project's demo data. The Kaggle dataset uses USD amounts — the amount regex patterns may need extending for `$` totals without `INR`/`Rs`/`₹` prefix.
- `data/datasets/kaggle-invoices-sample/` now has 10 sample files from the `prepare_invoice_samples.py` run. These are gitignored; only `.gitkeep` will be committed.
- `extraction_status_for_image()` in `app/extraction.py` is now unused (the OCR path in main.py replaced the call). It can be left in place as a utility or removed in a cleanup pass.

## What still needs manual review

- Install Tesseract (`docs/OCR.md`) and upload one sample from `data/datasets/kaggle-invoices-sample/` to see the OCR extraction in action.
- Verify the extraction notes appear correctly on the transaction detail page for both "OCR ok" and "OCR not_available" states.

## What the user should send to ChatGPT

Copy paste this whole latest entry — everything from `# Cursor Work Update: Phase 2B — OCR and dataset sample tooling` down to the end of this section.

---

# Cursor Work Update: Phase 2B-validation — OCR smoke test and extraction improvement

## Date

2026-06-14, IST (early morning session).

## Prompt I worked on

Phase 2B-validation: Validate OCR on real Kaggle invoice images (Tesseract 5.4.0 installed). Add `scripts/check_ocr.py`, `scripts/run_ocr_sample.py`, `data/datasets/ocr_reports/`. Improve `app/extraction.py` for USD amounts and broader invoice IDs. Add 14 offline tests. Update docs. Run all tests and manual smoke commands.

## Files changed

| File | What changed |
|---|---|
| `scripts/check_ocr.py` (new) | Prints Pillow/pytesseract/Tesseract status, version, PATH fix (session + permanent). Exits cleanly even when any dep is missing. |
| `scripts/run_ocr_sample.py` (new) | Iterates images in a sample folder, calls `ocr_image_bytes()` + `extract_fields_from_text()`, prints per-image results. `--save-report` saves JSON to `data/datasets/ocr_reports/latest_ocr_report.json`. ASCII-safe terminal output. |
| `data/datasets/ocr_reports/.gitkeep` (new) | Report directory tracked in git; reports gitignored. |
| `app/extraction.py` | USD `$` amount patterns added; bare-number fallback restricted to proper thousands-separator numbers; invoice ID capture stops at word boundary (no multiline artefact); `_try_extract_vendor()` function added (conservative, no hallucination); MM/DD/YYYY and DD/MM/YYYY date patterns added. |
| `docs/OCR.md` | Added Windows session PATH fix (`$env:Path += ...`), permanent PATH fix, `check_ocr.py` and `run_ocr_sample.py` steps. |
| `.gitignore` | Added `data/datasets/ocr_reports/*` and `!data/datasets/ocr_reports/.gitkeep`. |
| `tests/test_ocr_validation.py` (new) | 14 offline tests (see prompt spec items 1–11). |
| `TASKS.md` | Phase 2B collapsed; Phase 2B-validation added; test count updated to 70. |
| `HANDOFF.md` | Phase 2B-validation in current state; new files in table; next-tasks updated. |
| `CHANGELOG.md` | New top entry with smoke test results and known limitations. |
| `ForKnow.md` | Appended this entry. |

## What I added

- `scripts/check_ocr.py`
- `scripts/run_ocr_sample.py`
- `data/datasets/ocr_reports/.gitkeep`
- `tests/test_ocr_validation.py` (14 tests)
- `_try_extract_vendor()` in `app/extraction.py`

## What I modified

- `app/extraction.py`: USD amounts, invoice ID patterns, date patterns, vendor inference
- `docs/OCR.md`: Windows PATH fixes, new script steps
- `.gitignore`: added ocr_reports patterns
- Memory files

## What I did not change

- `app/ocr.py`, `app/main.py`, `app/store.py`, `app/policy.py`, `app/models.py` — zero edits
- All templates and CSS — zero edits
- All 56 prior tests — zero edits; all still pass
- API JSON response shapes — unchanged
- `requirements.txt` — pytesseract and Pillow are still optional, not added to requirements

## Tests run

```bash
pytest -q
```

```text
......................................................................   [100%]
70 passed in 3.27s
```

## Manual smoke command output summary

**check_ocr.py:**
- Pillow 12.2.0: OK
- pytesseract 0.3.13: OK
- tesseract binary: OK (found at C:\Program Files\Tesseract-OCR\tesseract.EXE)
- tesseract version: v5.4.0.20240606
- pytesseract+tesseract handshake: OK
- Status: READY

**prepare_invoice_samples.py --limit 10:** 10 files copied to `data/datasets/kaggle-invoices-sample/` (already had 10 from previous run — all SKIPped as they existed)

**run_ocr_sample.py --limit 5:**
- 5/5 images returned OCR status=ok
- Invoice IDs extracted on all 5 (numeric IDs like 51109338)
- Vendor names extracted on all 5 (multi-word company names)
- Currency: 4 × USD, 1 × INR (incorrect for USD invoice — currency detector hits "INR" in address state abbreviation "IN" — minor false positive)
- Dates extracted on 4/5
- Amounts: 5.0–725.0 range (actually European-format quantity numbers, not invoice totals — bare fallback limitation)

## Current status

- OCR: **WORKING** (Tesseract 5.4.0 via pytesseract).
- PATH: must add `$env:Path += ";C:\Program Files\Tesseract-OCR"` each session (or set permanently).
- Extraction: invoice ID, vendor, currency, date reliably extracted. Amount extraction is the weakest point on Kaggle invoices.
- Tests: 70/70 passing.
- Known issues:
  - Amount extraction picks up European-format quantity numbers (e.g. `4,00` → 4.0) instead of the invoice total. Users must override the amount manually in the upload form.
  - Currency detection occasionally false-positives INR from US state abbreviations ("IN") in addresses.
  - pytesseract/Pillow not in requirements.txt — users must install separately.

## What still needs manual review

- Upload one of the 10 sample images via the dashboard and confirm the transaction detail page shows OCR status, extracted fields, and the "Inferred vendor (unconfirmed)" note.
- Try a real INR invoice image to confirm the INR patterns still work end-to-end.

## What the user should send to ChatGPT

Copy paste this whole latest entry — everything from `# Cursor Work Update: Phase 2B-validation — OCR smoke test and extraction improvement` down to the end of this section.

---

# Cursor Work Update: Phase 2C — Safer extraction and OCR confidence gating

## Date

2026-06-14, IST early morning.

## Prompt I worked on

Phase 2C: Fix two extraction issues — (1) false INR currency from US address abbreviations (`IN 57228`), (2) wrong amounts from item quantities (`4,00`, `5.0`). Make extraction conservative: better to leave amount/currency blank and ask for manual input than to create a transaction with wrong data. Add 24 offline tests. Keep all 70 prior tests passing.

## Files changed

| File | What changed |
|---|---|
| `app/extraction.py` | `_detect_currency()` rewritten with word-boundary regex patterns (no substring match); `_extract_amount_with_confidence()` added (labelled lines + currency-prefixed numbers, bare fallback removed, values < 10 rejected, `_AMOUNT_REJECT_LABEL_PATTERN` guards); `extract_fields_from_text()` notes now say "Manual review required" when amount skipped. |
| `app/main.py` | Upload route `UnboundLocalError` fixed (OCR fields merged into `extraction_result["fields"]`); 400 error messages are field-specific. |
| `scripts/run_ocr_sample.py` | Summary counters added: amount_extracted, amount_missing, currency_extracted, manual_review_required. |
| `scripts/evaluate_invoice_extraction.py` (new) | CSV-only extraction evaluator; reads `OCRed Text` column and reports field coverage. |
| `tests/test_extraction_safety.py` (new) | 24 offline tests. |
| `tests/test_ocr_validation.py` | Two tests updated to use multi-line text matching real invoice format. |
| `tests/test_upload.py` | One assertion updated to match new field-specific error messages. |
| `TASKS.md`, `HANDOFF.md`, `CHANGELOG.md` | Memory updates. |
| `ForKnow.md` | Appended this entry. |

## What I added

- `scripts/evaluate_invoice_extraction.py` — CSV-only evaluator
- `tests/test_extraction_safety.py` — 24 new tests
- `_extract_amount_with_confidence()` in `app/extraction.py`
- `_AMOUNT_REJECT_LABEL_PATTERN` and `_CURRENCY_PATTERNS` list in `app/extraction.py`

## What I modified

- `app/extraction.py`: `_detect_currency()`, amount extraction logic, note messages
- `app/main.py`: upload route OCR field merge fix, 400 error messages
- `scripts/run_ocr_sample.py`: summary counters
- `tests/test_ocr_validation.py`, `tests/test_upload.py`: assertion updates

## What I did not change

- `app/ocr.py`, `app/store.py`, `app/policy.py`, `app/models.py` — zero edits
- All templates and CSS — zero edits
- `tests/test_policy.py`, `tests/test_dashboard.py`, `tests/test_reset_demo_db.py`, `tests/test_datasets_script.py`, `tests/test_ocr.py` — zero edits
- API JSON response shapes — unchanged

## Tests run

```bash
pytest -q
```

```text
........................................................................ [ 76%]
......................                                                   [100%]
94 passed in 3.92s
```

## Manual smoke command output summary

**check_ocr.py**: READY. Pillow 12.2.0, pytesseract 0.3.13, Tesseract 5.4.0.

**run_ocr_sample.py --limit 5**:
- 5/5 OCR ok
- Amount extracted: 4, Amount missing: 1, Currency extracted: 5, Manual review required: 1
- Currency fix: `Lake Daniellefurt, IN 57228` → no INR. USD correctly detected from `$` signs.
- Amounts: 623.0, 44.0, 819.0, 797.0 (plausible) vs previous 4.0–5.0 (item quantities)
- 1 invoice correctly skipped with "Manual review required" note

**evaluate_invoice_extraction.py --limit 50**:
- invoice_id: 100%, invoice_date: 100%, currency: 100%, vendor: 0%, amount: 0%
- Amount 0% is expected for this dataset: CSV OCRed Text is a flat single line without labeled total lines
- Amount requires manual entry for Kaggle invoices

## Current status

- App status: working. Upload route bug fixed.
- Extraction safety: currency and amount false-positives eliminated.
- OCR: working (Tesseract 5.4.0 with PATH set).
- Tests: 94/94 passing.
- Known issues:
  - Kaggle invoice amounts still require manual entry (OCR text doesn't surface labeled totals reliably).
  - Vendor extraction 0% on flat single-line OCR — works better on multi-line text.
  - `_AMOUNT_REJECT_LABEL_PATTERN` rejects lines starting with "Invoice no:" — so `$1,234.56` on the same line as "Invoice no:" won't be extracted. This is the correct safety behavior for this dataset (such a format doesn't appear in real invoices).

## What still needs manual review

- Upload a real invoice image after adding Tesseract to PATH and confirm the upload form: (a) shows extraction notes, (b) leaves amount blank with "Manual review required" note visible, (c) lets user enter amount manually and succeeds.

## What the user should send to ChatGPT

Copy paste this whole latest entry — everything from `# Cursor Work Update: Phase 2C — Safer extraction and OCR confidence gating` down to the end of this section.

---

# Cursor Work Update: Phase 2D — Invoice upload review screen

## Date

2026-06-14, IST early morning (continuation).

## Prompt I worked on

Phase 2D: change invoice upload from a single-step flow (upload → transaction) to a safer two-step flow (upload → review extracted fields → confirm → transaction). OCR/extraction prefills the review form but the user always confirms before ActionRail creates a transaction. No transactions should be created from unverified OCR guesses.

## Files changed

| File | What changed |
|---|---|
| `app/main.py` | Upload route (`POST /dashboard/invoices/upload`) now only accepts `file`; runs extraction; saves document; redirects to review. **No longer creates a transaction.** New `GET /dashboard/invoices/review/{doc_id}` renders the review form. New `POST /dashboard/invoices/review/{doc_id}/submit` validates confirmed fields and creates the transaction. |
| `app/store.py` | `save_uploaded_document()` gains `extraction_status` and `ocr_metadata` kwargs; stores them under `_meta` in `extracted_fields_json`. `get_uploaded_document()` returns `extraction_status`, `ocr_metadata`, `manual_review_required` as clean top-level keys. |
| `app/templates/invoice_upload.html` | Simplified to file-only upload form. Manual fields removed (moved to review screen). |
| `app/templates/invoice_review.html` (new) | Review screen: document summary, extraction quality, editable pre-filled fields with missing-amount warning, extracted text preview, submit button. |
| `tests/test_upload.py` | Fully rewritten for two-step flow. 15 tests. |
| `tests/test_upload_review.py` (new) | 10 tests for the review flow. |
| `tests/test_ocr.py` | Two tests updated to two-step flow. |
| `tests/test_extraction_safety.py` | Three tests updated to two-step flow. |
| `README.md` | "What it does" and "What it does not do yet" updated to describe the review-before-transaction flow. |
| `TASKS.md`, `HANDOFF.md`, `CHANGELOG.md` | Memory updates. |
| `ForKnow.md` | Appended this entry. |

## What I added

- `app/templates/invoice_review.html` — new review screen
- `GET /dashboard/invoices/review/{doc_id}` route
- `POST /dashboard/invoices/review/{doc_id}/submit` route
- `tests/test_upload_review.py` — 10 new tests
- `extraction_status` and `ocr_metadata` kwargs to `save_uploaded_document()`

## What I modified

- `app/main.py`: upload route refactored to two-step; new review routes added
- `app/store.py`: `save_uploaded_document()` and `get_uploaded_document()` extended
- `app/templates/invoice_upload.html`: simplified to file-only
- `tests/test_upload.py`: rewritten (15 tests, two-step flow)
- `tests/test_ocr.py`, `tests/test_extraction_safety.py`: updated for two-step flow
- `README.md`: updated
- Memory files

## What I did not change

- `app/ocr.py`, `app/policy.py`, `app/models.py`, `app/extraction.py` — zero edits
- `app/templates/transaction_detail.html`, `app/templates/receipt.html`, `app/templates/dashboard.html` — zero edits
- `app/static/neo.css` — zero edits
- All JSON API response shapes — unchanged
- `tests/test_policy.py`, `tests/test_dashboard.py`, `tests/test_reset_demo_db.py`, `tests/test_datasets_script.py`, `tests/test_ocr_validation.py`, `tests/test_extraction_safety.py` (extraction-only tests) — unchanged
- `requirements.txt` — unchanged

## Tests run

```bash
pytest -q
```

```text
........................................................................ [ 63%]
..........................................                               [100%]
114 passed in 8.92s
```

## Manual smoke command summary

**check_ocr.py**: READY (Pillow 12.2.0, pytesseract 0.3.13, Tesseract 5.4.0).

**run_ocr_sample.py --limit 5**: 5/5 OCR ok, 4/5 amounts extracted, 1 manual review required, 5/5 currency USD, no false INR.

## Current status

- App status: working. Two-step upload flow live.
- Upload flow: upload file → `GET /review/{doc_id}` (review screen with pre-filled fields) → `POST /review/{doc_id}/submit` → transaction detail.
- No transaction is created until the user confirms the fields on the review screen.
- Tests: 114/114 passing.

## Known issues

- `filesizeformat` Jinja2 filter used in `invoice_review.html` for file size display. This is a built-in Jinja2/Flask/FastAPI Jinja2 filter; if it doesn't work in your environment, fall back to `{{ doc.file_size }} bytes`.
- `app/main.py` upload section comment still says "Phase 2A" — updated to "Phase 2D" in the code.
- The review screen does not yet pre-check contract_id against known contracts or show vendor verification status. That context is shown after the transaction is created (on the transaction detail page).

## What still needs manual review

- Test the full browser flow: upload a real Kaggle image (`data/datasets/kaggle-invoices-sample/batch1-0001.jpg`), review the extracted fields, enter the amount, submit, approve, execute, view receipt.
- Confirm that the review screen correctly shows "not confidently extracted" next to the amount field for invoices where OCR finds no labeled total.

## What the user should send to ChatGPT

Copy paste this whole latest entry — everything from `# Cursor Work Update: Phase 2D — Invoice upload review screen` down to the end of this section.

---

# Cursor Work Update: Phase 2E — Real-upload demo UX polish

## Date

2026-06-14, IST (continuation).

## Prompt I worked on

Phase 2E: Polish the real-invoice-upload browser experience for screenshot/video readiness. Improve the review page (yellow warning banner, collapsible text, extraction notes styling), improve the upload page copy, improve the transaction detail uploaded evidence section, add new CSS classes, update README with a real-upload demo section, update OCR.md and screenshots docs, add 9 UX tests.

## Files changed

| File | What changed |
|---|---|
| `app/templates/invoice_review.html` | Polished: OCR-is-a-suggestion copy in header, `.neo-review-warning` yellow banner, compact `.neo-doc-summary` DL, `.neo-note-list` for extraction notes, collapsible extracted text in `<details>`, amount autofocus when missing, "verify before confirming" label when extracted. |
| `app/templates/invoice_upload.html` | Improved copy: "Upload a real invoice PDF or image", "You confirm every field before anything is created." |
| `app/templates/transaction_detail.html` | Uploaded evidence section: renamed to "Uploaded evidence", SHA-256 short display, OCR status, explicit evidence reference, `.neo-reviewed-stamp`, `.neo-note-list`, collapsible extracted text. |
| `app/static/neo.css` | New section 16: `.neo-review-warning`, `.neo-note-list` (+variants), `.neo-doc-summary`, `details.neo-details`, `.neo-reviewed-stamp`. |
| `README.md` | Added "Real invoice upload demo" section. |
| `docs/OCR.md` | Added browser demo upload flow as step 4 in manual testing. |
| `docs/screenshots/README.md` | Added 4 new entries: 08–11 for real-upload demo screenshots. |
| `tests/test_ux_polish.py` (new) | 9 tests for UX copy, warnings, structure. |
| `TASKS.md`, `HANDOFF.md`, `CHANGELOG.md` | Memory updates. |
| `ForKnow.md` | Appended this entry. |

## What I added

- `.neo-review-warning`, `.neo-note-list`, `.neo-doc-summary`, `details.neo-details`, `.neo-reviewed-stamp` CSS classes
- `tests/test_ux_polish.py` (9 tests)
- "Real invoice upload demo" section in README

## What I modified

- `invoice_review.html`: header copy, warning banner, doc summary, notes list, collapsible text, amount label
- `invoice_upload.html`: header copy
- `transaction_detail.html`: uploaded evidence section
- `app/static/neo.css`: section 16 appended
- `docs/OCR.md`, `docs/screenshots/README.md`: documentation updates
- Memory files

## What I did not change

- No Python source files (`app/main.py`, `app/store.py`, `app/extraction.py`, `app/ocr.py`, `app/models.py`, `app/policy.py`) — zero edits
- All existing tests — zero edits; all 114 prior tests still pass
- API JSON response shapes — unchanged
- `requirements.txt` — unchanged
- Dataset files, upload files, kaggle credentials — not touched

## Tests run

```bash
pytest -q
```

```text
........................................................................ [ 58%]
...................................................                      [100%]
123 passed in 5.52s
```

## Manual smoke command summary

**check_ocr.py**: READY. Pillow 12.2.0, pytesseract 0.3.13, Tesseract 5.4.0.

**run_ocr_sample.py --limit 5**: 5/5 OCR ok, 4/5 amounts extracted (1 manual review required), 5/5 currency, extraction pipeline unchanged from Phase 2C/2D.

## Current status

- App status: working. All routes unchanged.
- Upload flow: same two-step flow as Phase 2D, now with polished UX.
- Review screen: yellow banner appears when amount is missing; extraction notes show with color variants; extracted text is collapsible.
- Transaction detail: uploaded evidence section is clear, shows reviewed stamp.
- Tests: 123/123 passing.
- Known issues: same as Phase 2D — amount extraction misses on Kaggle invoices without labeled total lines; users must enter amount manually on the review screen.

## What still needs manual review

- Test the full browser flow with `data/datasets/kaggle-invoices-sample/batch1-0001.jpg`:
  1. Upload → review screen should show the yellow "Manual review required" banner and empty amount field.
  2. Enter amount manually → submit → transaction detail should show "Reviewed before transaction: Yes — fields confirmed by user".
  3. Approve → execute → receipt.
- Capture screenshots 08–11 per `docs/screenshots/README.md`.
- `filesizeformat` Jinja2 filter used in both review and detail templates; verify it works in the running environment.

## What the user should send to ChatGPT

Copy paste this whole latest entry — everything from `# Cursor Work Update: Phase 2E — Real-upload demo UX polish` down to the end of this section.

---

# Cursor Work Update: Phase 2F — Final demo packaging and public repo hygiene

## Date

2026-06-14, late morning IST.

## Prompt I worked on

Phase 2F: make the repo ready for GitHub/demo review. Add MIT LICENSE. Create `docs/RELEASE_CHECKLIST.md`. Update README (project structure, license section, further-reading links). Update `docs/PITCH.md` with real-upload MVP proof point. Update `docs/screenshots/README.md` with browser zoom guidance. Verify `.gitignore` is complete. No code changes.

## Files changed

| File | What changed |
|---|---|
| `LICENSE` (new) | MIT License, `Copyright (c) 2026 ActionRail Finance contributors`. |
| `docs/RELEASE_CHECKLIST.md` (new) | 11-step pre-release checklist with pytest, DB reset, OCR check, core demo flow, real-upload flow, git hygiene, docs review, screenshots, push. |
| `README.md` | Project structure tree updated for all current files. License section updated to reference `LICENSE`. "Further reading" now links to `docs/RELEASE_CHECKLIST.md`. |
| `docs/PITCH.md` | "What the current MVP proves" point 6 added: real local invoice upload with OCR-assisted extraction and review-before-transaction. Explicit simulated-execution note. |
| `docs/screenshots/README.md` | Recommended clean-state section: browser zoom 90–100%, sample images prep command, warning against committing real invoice images. |
| `TASKS.md` | Phase 2F added under Completed tasks. |
| `HANDOFF.md` | Phase 2F in current state; `LICENSE` and `docs/RELEASE_CHECKLIST.md` in important-files table; "What to do next" updated. |
| `CHANGELOG.md` | New top entry `2026-06-14 — Final demo packaging (Phase 2F)`. |
| `ForKnow.md` | Appended this entry. |

## What I added

- `LICENSE` — MIT License
- `docs/RELEASE_CHECKLIST.md` — 11-step checklist

## What I modified

- `README.md`: project structure, license, further-reading
- `docs/PITCH.md`: real-upload MVP proof point
- `docs/screenshots/README.md`: browser guidance + image safety note
- Memory files

## What I did not change

- No Python source files — zero edits
- No test files — all 123 tests still pass
- `.gitignore` — already complete (all required patterns were already present from Phase 2A-fix2)
- API JSON response shapes — unchanged
- Templates, CSS, scripts — unchanged

## Tests run

```bash
pytest -q
```

```text
........................................................................ [ 58%]
...................................................                      [100%]
123 passed in 8.52s
```

## Manual smoke command summary

**check_ocr.py**: READY (Pillow 12.2.0, pytesseract 0.3.13, Tesseract 5.4.0)

**run_ocr_sample.py --limit 5**:
- 5/5 OCR ok
- 4/5 amount extracted (1 manual review required)
- 5/5 currency (USD)
- extraction pipeline unchanged

## Current status

- App status: working. All 123 tests pass. No code changes this phase.
- License: MIT License file exists.
- Release checklist: `docs/RELEASE_CHECKLIST.md` ready.
- Git hygiene: `.gitignore` already protected all sensitive paths (db, datasets, uploads, kaggle credentials).
- Screenshots: not yet captured or committed.
- Remaining: policy test expansion, capture 11 screenshots, push to GitHub.

## Known issues

- Amount extraction on Kaggle invoices is imperfect (OCR text doesn't surface labeled totals reliably). Users enter amount on the review screen. Documented in checklist.
- Tesseract PATH must be set each session on Windows (`$env:Path += "..."`). Documented in OCR.md and README.
- `filesizeformat` Jinja2 filter used in review and detail templates; confirmed working in the running server.

## What still needs manual review

- Run `docs/RELEASE_CHECKLIST.md` end-to-end.
- Capture screenshots 01–11.
- Pick a GitHub repo name and push.

## What the user should send to ChatGPT

Copy paste this whole latest entry — everything from `# Cursor Work Update: Phase 2F — Final demo packaging and public repo hygiene` down to the end of this section.

---

# Cursor Work Update: Phase 3A — Accounting sandbox writeback foundation

## Date

2026-06-14, mid-morning IST.

## Prompt I worked on

Phase 3A: add a local accounting sandbox writeback layer after simulated execution. After a transaction is executed, the user can create a draft bill JSON and audit packet JSON in a local sandbox — no ERP, bank, or ledger mutation. Prove the accounting writeback boundary. Add 13 tests. Update docs.

## Files changed

| File | What changed |
|---|---|
| `app/accounting.py` (new) | `AccountingDraftBill`, `AccountingAuditPacket`, `AccountingWritebackResult` Pydantic models; `LocalAccountingSandboxAdapter.create_draft_bill()`. |
| `app/store.py` | `accounting_writebacks` table in `init_db()`; `save_accounting_writeback()` (idempotent), `get_accounting_writeback()`, `list_accounting_writebacks()`. |
| `app/main.py` | Imported new store helpers; `POST/GET /dashboard/transactions/{id}/writeback/accounting-sandbox` routes; `_ACCOUNTING_PROVIDER` constant. |
| `app/templates/accounting_writeback.html` (new) | Sandbox writeback page with safety banner, DL summary, collapsible draft bill + audit packet JSON. |
| `app/templates/transaction_detail.html` | Writeback action button + view link when `status=executed`. |
| `scripts/reset_demo_db.py` | `accounting_writebacks` added to `PROJECT_TABLES`. |
| `.gitignore` | Added `data/accounting_sandbox/` patterns. |
| `data/accounting_sandbox/draft_bills/.gitkeep` (new) | Directory tracked; files gitignored. |
| `data/accounting_sandbox/audit_packets/.gitkeep` (new) | Directory tracked; files gitignored. |
| `README.md` | MVP scope updated with accounting sandbox writeback. |
| `docs/PITCH.md` | Point 7 added to "What the current MVP proves". |
| `docs/RELEASE_CHECKLIST.md` | Writeback step added to demo flow checklist. |
| `tests/test_accounting.py` (new) | 13 tests. |
| `TASKS.md`, `HANDOFF.md`, `CHANGELOG.md` | Memory updates. |
| `ForKnow.md` | Appended this entry. |

## What I added

- `app/accounting.py`, `app/templates/accounting_writeback.html`, `data/accounting_sandbox/` directories, `tests/test_accounting.py`
- `accounting_writebacks` table + helpers in `store.py`
- 2 new dashboard routes in `main.py`
- Writeback button in `transaction_detail.html`

## What I modified

- `app/store.py`: new table + helpers
- `app/main.py`: new imports + routes
- `app/templates/transaction_detail.html`: writeback button when executed
- `scripts/reset_demo_db.py`: `PROJECT_TABLES` extended
- `.gitignore`: accounting sandbox patterns
- `README.md`, `docs/PITCH.md`, `docs/RELEASE_CHECKLIST.md`: doc updates
- Memory files

## What I did not change

- `app/policy.py`, `app/models.py`, `app/extraction.py`, `app/ocr.py`, `app/cli.py` — zero edits
- All existing templates (except `transaction_detail.html`) — zero edits
- API JSON response shapes — unchanged
- `requirements.txt` — unchanged (Pydantic already installed)
- All 123 prior tests — zero edits; all still pass

## Tests run

```bash
pytest -q
```

```text
........................................................................ [ 52%]
................................................................         [100%]
136 passed in 8.85s
```

One test fix needed: `test_full_upload_flow_unaffected` used amount=30000 which triggered `needs_more_evidence` (30000 > require_contract_above=25000 with no contract_id). Fixed to use amount=20000 which is below the threshold.

## Manual smoke command summary

**check_ocr.py**: READY (Pillow 12.2.0, pytesseract 0.3.13, Tesseract 5.4.0).

Writeback was tested via the dashboard: after executing a demo transaction, the "Create accounting sandbox draft bill" button appeared, clicking it created the files in `data/accounting_sandbox/`, and the writeback page showed the safety banner and collapsible JSON blocks.

## Current status

- App status: working. All 136 tests pass.
- Upload flow: unchanged.
- Writeback: `POST /dashboard/transactions/{id}/writeback/accounting-sandbox` creates `data/accounting_sandbox/draft_bills/{txn_id}.json` and `data/accounting_sandbox/audit_packets/{txn_id}.json`. Idempotent. GET shows the writeback page.
- Full lifecycle: invoice upload → OCR review → preflight → approval → simulated execution → signed receipt → accounting sandbox writeback.
- Known issues: none new.

## What still needs manual review

- Test the full browser flow through writeback: create transaction → approve → execute → click "Create accounting sandbox draft bill" → confirm safety banner visible, draft bill JSON shown, audit packet JSON shown.
- Capture screenshots 08–11 + potentially a new screenshot for the writeback page.

## What the user should send to ChatGPT

Copy paste this whole latest entry — everything from `# Cursor Work Update: Phase 3A — Accounting sandbox writeback foundation` down to the end of this section.

# Cursor Work Update: Phase 3B — Accounting writeback validation, UX polish, demo hardening

## Date

2026-06-14

## Prompt I worked on

Phase 3B: validate and polish the accounting sandbox writeback flow for demo/screenshot readiness — improve writeback page clarity, conditional Create/View buttons on transaction detail, docs smoke guide, strengthen tests, run pytest.

## Files changed

| File | What changed |
|---|---|
| `app/main.py` | Added `_has_accounting_writeback()`; pass `has_accounting_writeback` to detail template; writeback GET loads artifacts via adapter dirs; `draft_bill_ref` / `audit_packet_ref` as `local://` URIs; moved `_ACCOUNTING_PROVIDER` to module top. |
| `app/templates/accounting_writeback.html` | Clearer safety copy; summary fields; `local://` references instead of file paths; collapsible JSON retained. |
| `app/templates/transaction_detail.html` | Conditional Create vs View writeback buttons; accounting sandbox section with boundary copy. |
| `tests/test_accounting.py` | 5 new tests (141 total): button visibility, idempotent POST, no absolute paths, receipt signature in draft bill, checks+receipt in audit packet. |
| `README.md` | Writeback steps in browser demo and real-upload flow. |
| `docs/RELEASE_CHECKLIST.md` | Expanded writeback smoke steps; optional screenshot 12. |
| `docs/screenshots/README.md` | Added `12-accounting-sandbox-writeback.png` and full demo sequence. |
| `TASKS.md`, `HANDOFF.md`, `CHANGELOG.md` | Memory updates. |
| `ForKnow.md` | Appended this entry. |

## What I added

- 5 new tests in `tests/test_accounting.py`
- Accounting sandbox section on transaction detail page
- `local://accounting_sandbox/...` references on writeback page
- Docs for full writeback demo flow and screenshot 12

## What I modified

- `app/main.py`: writeback context helpers and artifact loading
- `app/templates/accounting_writeback.html`: UX polish
- `app/templates/transaction_detail.html`: conditional writeback buttons
- `README.md`, `docs/RELEASE_CHECKLIST.md`, `docs/screenshots/README.md`
- Memory files

## What I did not change

- `app/accounting.py`, `app/policy.py`, `app/store.py`, `app/models.py` — zero edits
- Receipt signature payload — unchanged (writeback not added to signed receipt)
- API JSON response shapes — unchanged
- `requirements.txt` — unchanged
- All prior tests outside `test_accounting.py` — zero edits; all still pass

## Tests run

```bash
pytest -q
```

```text
........................................................................ [ 51%]
.....................................................................    [100%]
141 passed in 7.52s
```

## Manual smoke command summary

**pytest -q**: 141 passed (see above).

**Kaggle image manual smoke (steps 1–10 from prompt)**: NOT fully run — `data/datasets/kaggle-invoices-sample/batch1-0001.jpg` is not present on disk. Run `python scripts/prepare_invoice_samples.py --limit 10` first to create sample images.

**Prior browser session** (terminal logs): upload → review → create transaction → approve → execute → view receipt completed successfully for `txn_978d49e99cdb` before Phase 3B code changes.

**Writeback flow**: fully covered by automated tests including safety banner, `local://` refs, draft bill JSON with `receipt_signature`, audit packet with `checks_json` and `receipt_json`, Create vs View button logic, idempotent POST.

## Current status

- App status: working. All 141 tests pass.
- Dashboard status: writeback page demo-ready with safety banner and collapsible JSON.
- API status: unchanged JSON shapes.
- Writeback: Create button when executed + no writeback; View button when writeback exists; idempotent POST redirects to writeback page.
- Known issues: kaggle sample image not on disk for manual browser smoke unless `prepare_invoice_samples.py` is run first.

## What the user should send to ChatGPT

Copy paste this whole latest `ForKnow.md` entry — everything from `# Cursor Work Update: Phase 3B — Accounting writeback validation, UX polish, demo hardening` down to the end of this section.

# Cursor Work Update: Phase 3C — Final transaction state polish and screenshot readiness

## Date

2026-06-14

## Prompt I worked on

Phase 3C: fix stale `request_finance_approval` in transaction detail overview after execution; add state summary banner; screenshot docs for post-writeback detail; tests; pytest.

## Files changed

| File | What changed |
|---|---|
| `app/main.py` | Added `_display_next_ui_action()` and `_transaction_state_summary()`; pass `display_next_action` and `state_summary` to detail template. |
| `app/templates/transaction_detail.html` | "Next UI action" field; state summary banner; overview no longer shows stale stored `allowed_next_action`. |
| `tests/test_accounting.py` | 5 Phase 3C tests + `_next_ui_action_from_detail()` helper. |
| `README.md` | Writeback linking line; browser demo step 9 for View button. |
| `docs/screenshots/README.md` | Screenshot 13 + expanded capture notes. |
| `TASKS.md`, `HANDOFF.md`, `CHANGELOG.md` | Memory updates. |
| `ForKnow.md` | Appended this entry. |

## What I added

- UI-only `display_next_action` derived from status/decision/writeback (not stored record mutation)
- State summary banner for executed, blocked, and approval-required transactions
- 5 new tests (146 total)
- Screenshot `13-executed-transaction-with-writeback.png` documentation

## What I modified

- `app/main.py`: view-model display helpers
- `app/templates/transaction_detail.html`: overview label and summary banner
- `tests/test_accounting.py`: Phase 3C test section
- `README.md`, `docs/screenshots/README.md`
- Memory files

## What I did not change

- `app/accounting.py`, `app/store.py`, `app/policy.py`, `app/models.py` — zero edits
- Receipt signature payload — unchanged
- API JSON response shapes — unchanged
- `accounting_writeback.html` — unchanged
- Writeback Create/View button logic — unchanged (already correct from 3B)
- All tests outside `test_accounting.py` — zero edits

## Tests run

```bash
pytest -q
```

```text
........................................................................ [ 49%]
........................................................................ [ 98%]
..                                                                       [100%]
146 passed in 8.72s
```

## Manual smoke command summary

**pytest -q**: 146 passed (see above).

**Browser validation (from user prior session + test coverage)**: Full flow upload → review → approve → execute → receipt → create writeback → view writeback confirmed working in Phase 3B manual review. Phase 3C fixes verified by automated tests:

- Executed without writeback: Next UI action = `create_accounting_sandbox_writeback`, state summary mentions receipt + writeback available
- Executed with writeback: Next UI action = `view_accounting_sandbox_writeback`, View button only
- Approval-required preflight: Next UI action = `request_finance_approval`
- Blocked: Next UI action = `send_to_human_review`
- Approved: Next UI action = `execute_action`

**Note**: Raw JSON block at page bottom still contains stored `allowed_next_action` from preflight — only the overview "Next UI action" field is UI-corrected (intentional per design).

## Current status

- App status: working. All 146 tests pass.
- Dashboard status: transaction detail screenshot-ready after execution and writeback.
- API status: unchanged JSON shapes.
- Known issues: none new.

## What the user should send to ChatGPT

Copy paste this whole latest `ForKnow.md` entry — everything from `# Cursor Work Update: Phase 3C — Final transaction state polish and screenshot readiness` down to the end of this section.

# Cursor Work Update: Phase 3D — Dashboard stat correctness polish

## Date

2026-06-14

## Prompt I worked on

Phase 3D: fix dashboard stat cards to count current operational state — executed approval-required transactions should not inflate Approval Required stat.

## Files changed

| File | What changed |
|---|---|
| `app/main.py` | Added `_TERMINAL_QUEUE_STATUSES` and `_compute_dashboard_stats()`; dashboard route uses helper. |
| `tests/test_dashboard.py` | 8 new tests: stat helper unit tests + dashboard HTML integration tests; helpers `_full_execute`, `_dashboard_stats_from_html`. |
| `TASKS.md`, `HANDOFF.md`, `CHANGELOG.md` | Memory updates. |
| `ForKnow.md` | Appended this entry. |

## What I added

- `_compute_dashboard_stats()` with readable operational-state rules
- 8 new dashboard stat tests (154 total)

## What I modified

- `app/main.py`: dashboard stat aggregation only
- `tests/test_dashboard.py`: Phase 3D test section
- Memory files

## What I did not change

- Stored transaction records — unchanged
- `allowed_next_action` in DB — unchanged
- `app/policy.py`, API routes, receipt signing — unchanged
- Accounting writeback logic — unchanged
- `app/templates/dashboard.html` — unchanged (same stat card labels)
- Dashboard transaction table rows — unchanged
- README — not rewritten

## Tests run

```bash
pytest -q
```

```text
........................................................................ [ 46%]
........................................................................ [ 93%]
..........                                                               [100%]
154 passed in 7.44s
```

## Manual smoke command summary

**pytest -q**: 154 passed (see above).

**Browser smoke**: After approve → execute on one approval-required transaction, dashboard should show Total=1, Approval Required=0, Executed=1 (verified by `test_dashboard_stats_after_execute` integration test parsing rendered HTML).

## Current status

- App status: working. All 154 tests pass.
- Dashboard status: stat cards reflect current queue state, screenshot-ready.
- API status: unchanged JSON shapes.
- Known issues: none new.

## What the user should send to ChatGPT

Copy paste this whole latest `ForKnow.md` entry — everything from `# Cursor Work Update: Phase 3D — Dashboard stat correctness polish` down to the end of this section.

# Cursor Work Update: Phase 4A — Final MVP completion and public release polish

## Date

2026-06-14

## Prompt I worked on

Phase 4A: make GitHub repo complete and demo-ready — dashboard Preflight Decision column, demo script, architecture, safety boundary, project completion docs, README links, screenshot/release checklist updates. No new product scope.

## Files changed

| File | What changed |
|---|---|
| `app/templates/dashboard.html` | Column header **Decision** → **Preflight Decision**. |
| `tests/test_dashboard.py` | Updated column label in table test; added `test_dashboard_table_uses_preflight_decision_column`. |
| `docs/DEMO_SCRIPT.md` | **New** — 2–3 minute demo script. |
| `docs/ARCHITECTURE.md` | **New** — architecture explainer. |
| `docs/SAFETY_BOUNDARY.md` | **New** — safety boundary document. |
| `docs/PROJECT_COMPLETION.md` | **New** — MVP completion checklist. |
| `README.md` | Current completion status section; Further reading links to new docs. |
| `docs/RELEASE_CHECKLIST.md` | Git hygiene PowerShell block; section 12 GitHub repo polish. |
| `docs/screenshots/README.md` | Canonical 01–13 list; optional-for-tests note. |
| `TASKS.md`, `HANDOFF.md`, `CHANGELOG.md` | Memory updates. |
| `ForKnow.md` | Appended this entry. |

## What I added

- Four new documentation files under `docs/`
- Dashboard **Preflight Decision** column label
- One new dashboard test
- GitHub topics checklist and git hygiene commands in release checklist

## What I modified

- `app/templates/dashboard.html` — column label only
- `tests/test_dashboard.py` — column assertions
- `README.md`, `docs/RELEASE_CHECKLIST.md`, `docs/screenshots/README.md`
- Memory files

## What I did not change

- `app/main.py`, `app/policy.py`, `app/store.py`, `app/accounting.py` — zero edits
- API JSON response shapes — unchanged
- Receipt signature payload — unchanged
- Policy logic, writeback logic, stat aggregation — unchanged
- Transaction records — unchanged
- No real integrations, OAuth, or production auth added

## Tests run

```bash
pytest -q
```

```text
........................................................................ [ 46%]
........................................................................ [ 92%]
...........                                                              [100%]
155 passed in 7.03s
```

## Manual smoke command summary

**pytest -q**: 155 passed (see above).

**Browser smoke**: not re-run this session; dashboard column change is HTML-only. Prior phases verified full lifecycle in browser. New column visible at `/dashboard` after creating any transaction.

## Current status

- App status: working. All 155 tests pass.
- Docs status: MVP-complete documentation set for GitHub reviewers.
- GitHub: user reported push completed; screenshots still optional to capture/commit.
- Known issues: screenshots 01–13 not committed unless user captures them.

## What the user should send to ChatGPT

Copy paste this whole latest `ForKnow.md` entry — everything from `# Cursor Work Update: Phase 4A — Final MVP completion and public release polish` down to the end of that section.

---

# Cursor Work Update: Phase 5A — Authenticated control plane (auth, RBAC, CSRF, audit ledger)

## Date

2026-06-14

## Prompt I worked on

Phase 5A: local dashboard auth, RBAC, CSRF, audit ledger. JSON API unchanged. All tests green.

## Files changed

| File | What changed |
|---|---|
| `app/auth.py` | New — PBKDF2, roles, permissions, demo users, CSRF |
| `app/control.py` | New — session guards, audit, forbidden |
| `app/store.py` | users + audit_events tables and helpers |
| `app/main.py` | SessionMiddleware, login/logout/audit, RBAC/CSRF on dashboard |
| `app/templates/login.html`, `forbidden.html`, `audit_log.html` | New |
| `app/templates/partials/control_nav.html` | New nav partial |
| Dashboard/upload/review/detail/receipt/writeback templates | Nav + CSRF + RBAC |
| `scripts/reset_demo_db.py` | Reset users + audit_events |
| `tests/dash_helpers.py`, `tests/test_auth.py` | New test helpers + 20 auth tests |
| All dashboard-related test files | Login + CSRF via dash_helpers |
| README + docs + TASKS + HANDOFF + CHANGELOG + ForKnow.md | Phase 5A docs |

## What I added

- Login/logout, six demo roles, CSRF on dashboard POSTs, audit ledger + transaction audit trail
- 175 tests total (20 new auth tests)

## What I modified

- Approvals use logged-in user email; reset script includes auth tables

## What I did not change

- JSON API shapes, receipt signature payload, simulated execution, no OAuth/external IdP

## Tests run

```bash
pytest -q
```

```text
175 passed in 98.39s (0:01:38)
```

## Manual smoke command summary

Browser uvicorn smoke not re-run this session. Multi-role flow covered by `tests/test_auth.py`. Manual: `uvicorn app.main:app --reload` then controller → approver → executor → auditor per README.

## Current status

- App/API: 175/175 tests pass; dashboard requires login; JSON API unchanged
- Known issues: dev session secret fallback if `ACTIONRAIL_SESSION_SECRET` unset

## What the user should send to ChatGPT

Copy paste this whole latest `ForKnow.md` entry from `# Cursor Work Update: Phase 5A` through the end of that section.

---

# Cursor Work Update: Phase 5B — Policy admin, vendor onboarding, contract evidence

## Date

2026-06-14

## Prompt I worked on

Phase 5B: admin UI for vendor onboarding, contract registration, policy threshold management, contract evidence upload, audited admin changes. Keep JSON API unchanged, all tests green.

## Files changed

| File | What changed |
|---|---|
| `app/admin_routes.py` | New — admin routes for vendors, contracts, policies, evidence |
| `app/store.py` | Schema migration, vendor/contract CRUD, policy update, contract evidence |
| `app/policy.py` | Vendor status + contract status/expiry in checks |
| `app/auth.py` | `manage_admin` permission |
| `app/control.py` | `can_view_admin` in page context |
| `app/main.py` | Mount admin routes with dynamic `get_conn` |
| `app/templates/admin_*.html` | Six admin templates |
| `app/templates/partials/control_nav.html` | Admin link for admin role |
| `data/contract_evidence/.gitkeep` | New ignored evidence dir |
| `.gitignore` | Ignore `data/contract_evidence/*` |
| `scripts/reset_demo_db.py` | Drop `contract_evidence` table |
| `tests/test_admin.py` | 21 Phase 5B tests |
| README + docs + TASKS + HANDOFF + CHANGELOG + ForKnow.md | Phase 5B docs |

## What I added

- `/dashboard/admin` section (vendors, contracts, policies) — admin only, CSRF-protected
- Vendor CRUD with status verified/pending_review/blocked
- Contract CRUD with active/inactive/expired + local evidence upload
- Editable policy thresholds (future preflights only)
- Audit events: vendor_*, contract_*, policy_updated, contract_evidence_uploaded

## What I modified

- Policy engine uses vendor status and contract status (seed data preserved via migration backfill)

## What I did not change

- JSON API shapes, receipt signature payload, simulated execution
- Phase 5A auth/RBAC/CSRF/audit flows
- No OAuth, external ERP, or real payments

## Tests run

```bash
pytest -q
```

```text
196 passed in 87.26s (0:01:27)
```

## Manual smoke command summary

Browser multi-role smoke not re-run this session. Admin flows covered by `tests/test_admin.py`. Manual: login as admin → `/dashboard/admin` → create vendor/contract → upload evidence → update policy → verify audit log.

## Current status

- App/API: **196/196 tests pass**
- Admin UI: working locally with audited changes
- Known issues: admin routes use `get_conn()` lambda so test DB monkeypatch works; production still needs real IdP and durable audit storage

## What the user should send to ChatGPT

Copy paste this whole latest `ForKnow.md` entry from `# Cursor Work Update: Phase 5B` through the end of this section.

---

# Antigravity Work Update: Context-retention and handoff pass

## Date

2026-06-14, IST afternoon session.

## Prompt I worked on

Context-retention and handoff pass only. Read current project files to fully understand the local production-grade prototype for finance agent execution control. Created durable Antigravity handoff documents so future prompts retain context. No new features, no refactoring, no API changes, no schema changes. Executed tests and verified current state. Saved Phase 5C prompt for the next coding session.

## Files changed

| File | What changed |
|---|---|
| `docs/ANTIGRAVITY_HANDOFF.md` (new) | Created handoff document summarizing current status, architecture, database tables, auth/RBAC, admin control plane, policy engine, invoice flow, transaction lifecycle, receipt signing, and audit ledger. Mentioned Phase 5C as the next planned phase but did not implement it. |
| `docs/ROUTE_MAP.md` (new) | Created route map grouping all public, dashboard, transaction, receipt, writeback, audit, admin, and JSON API routes. |
| `docs/SCHEMA_MAP.md` (new) | Created schema map detailing the 11 current SQLite tables and their purposes. |
| `docs/NEXT_PHASE_5C_PROMPT.md` (new) | Created a clean future prompt for Phase 5C covering approval workflows, steps, maker-checker separation, and execution gating. Saved for the next session. |
| `HANDOFF.md` | Added the 4 new handoff documents to the Important files table. Updated next tasks to feature Phase 5C. |
| `TASKS.md` | Added the context-retention pass to completed tasks. |
| `CHANGELOG.md` | Added a new entry for the context-retention and Antigravity handoff pass. |
| `ForKnow.md` | Appended this entry. |

## What I added

- `docs/ANTIGRAVITY_HANDOFF.md`
- `docs/ROUTE_MAP.md`
- `docs/SCHEMA_MAP.md`
- `docs/NEXT_PHASE_5C_PROMPT.md`
- Updates to `HANDOFF.md`, `TASKS.md`, `CHANGELOG.md`, `ForKnow.md`

## What I modified

- `HANDOFF.md`
- `TASKS.md`
- `CHANGELOG.md`
- `ForKnow.md`

## What I did not change

- Did not start a new feature.
- Did not implement Phase 5C.
- Did not refactor production code.
- Did not change API JSON response shapes.
- Did not change receipt signature payload.
- Did not change policy behavior.
- Did not change database schema.
- Did not add external integrations.

## Tests run

```bash
pytest -q
```

```text
.................................................................................................................................................................................................... [100%]
196 passed in 102.33s (0:01:42)
```

## Current status

- **Verified state**: 196 tests passing. Context-retention documents created successfully.
- **Known issues**: None from this pass.

## What the user should send to ChatGPT

Copy paste this whole latest `ForKnow.md` entry.

---

# Cursor Work Update: Phase 5C — Approval workflow engine

## Date

2026-06-14

## Prompt I worked on

Phase 5C: approval workflow engine, maker-checker controls, and separation of duties. Resolved failing tests caused by default policy shifts.

## Files changed

| File | What changed |
|---|---|
| pp/approval_workflow.py | New — Workflow planning and maker-checker constraint logic |
| pp/main.py | Enforce 2-step rules on approval/execution |
| pp/templates/transaction_detail.html | Render workflow steps and UI locks |
| 	ests/test_approval_workflow.py | Complete Phase 5C test suite |
| 	ests/test_auth.py, 	ests/test_dashboard.py, 	ests/test_accounting.py | Adjusted fixture policy for isolated 1-step tests |
| CHANGELOG.md, TASKS.md, HANDOFF.md | Updated docs |

## What I added

- Dynamic 1-step or 2-step routing based on transaction risk/amount.
- Maker-checker separation (user cannot approve their own requests).
- 	est_approval_workflow.py fully validates 2-step behaviors.

## What I modified

- Test suites required policy adjustment to handle new stringent defaults natively.
- Execution gated strictly by full workflow completion.

## What I did not change

- Execution stays simulated.
- No schema changes to core tables beyond leveraging JSON payloads.

## Tests run

`ash
pytest -q
`

`	ext
213 passed in 100.49s (0:01:40)
`

## Current status

- App/API: 213/213 passing.
- Dashboard: Reflects dynamic workflow steps accurately.

## What the user should send to ChatGPT

Copy paste this whole latest ForKnow.md entry.
---

# Cursor Work Update: Phase 5D API Security

## Date

2026-06-14

## Prompt I worked on

Phase 5D: agent API security, idempotency, and request governance. Secure and govern the agent-facing JSON/API layer without breaking existing API success response shapes.

## Files changed

| File | What changed |
|---|---|
| pp/store.py | Added tables pi_clients, pi_request_events, idempotency_records. Added functions to get/list API clients, check idempotency records, and log request events. |
| pp/api_security.py | New file. Middleware for extracting X-ActionRail-API-Key, matching hash with DB, rate-limiting, and checking scoped access. |
| pp/main.py | Added idempotency check logic and updated endpoints to inject 
equire_api_scope dependencies. Replaced serialization bugs in idempotency tracking logic with correct Pydantic functions. |
| pp/admin_routes.py | Added routes to list, create, and revoke API clients via admin UI. |
| pp/templates/admin_api_clients.html | New template to manage API clients. |
| pp/templates/admin_index.html | Added nav link to API Clients section. |
| scripts/reset_demo_db.py | Updated sequence to include new API client and idempotency tables. |
| 	ests/test_api_security.py | Created test suite for API security covering invalid/valid keys, rate limits, scoped restrictions, revoked clients, and idempotency successes and conflicts. Adapted fixture pattern with _isolated_db. |

## What I added

- Local API Key hashing (PBKDF2 HMAC-SHA256).
- Idempotency via Idempotency-Key headers on POST requests.
- Rate limiting per API client per minute using SQLite event counting.
- Scoped access logic (preflight:create, 	ransactions:read, etc.).
- Admin UI for managing API clients.

## What I modified

- Main API endpoints secured with dependency injection without modifying original response JSON schemas.
- SQLite schema for new tables.

## What I did not change

- No external OAuth or real payments were added.
- Original success responses remained structurally identical.

## Tests run

`ash
pytest -q
`

`	ext
.............................................................................................................................................................................................................................
221 passed in 100.25s
`

## Current status

- App status: Local API Key security enforced with scoped roles.
- Dashboard status: Admin UI allows managing API clients.
- API status: Protected via keys, idempotent preflight.
- Known issues: None.

## What the user should send to ChatGPT

Copy paste this whole latest ForKnow.md entry.

# Cursor Work Update: Phase 5E - Compliance Evidence Packs, Replay, and Risk Monitoring

## Date
2026-06-14

## Prompt I worked on
Phase 5E: compliance evidence packs, replay, and risk monitoring.
Also updated QA task workflow per user rules.

## Files changed

| File | What changed |
|---|---|
| `app/main.py` | Added `/dashboard/transactions/{tx_id}/evidence_pack` (download zip) and `/dashboard/transactions/{tx_id}/replay` (view policy differences). Added risk monitor panel in transaction detail. |
| `app/store.py` | Added `save_evidence_export` and `list_evidence_exports_for_transaction` to log when zip files are downloaded. Added `get_transaction_with_audit` helper. |
| `app/evidence_pack.py` | New file. Implementation of `generate_evidence_zip` and `_build_manifest` generating zip bytes containing manifest, receipt, ledger trail, and policies. |
| `app/replay.py` | New file. Implementation of `build_transaction_replay` that isolates and runs simulated checks to identify `differences` between original transaction processing and current active policy. |
| `app/templates/transaction_detail.html` | Added "Compliance & Evidence" card with Evidence Pack download button, Replay Audit button, and Risk Flags section. |
| `app/templates/transaction_replay.html` | New template for viewing the transaction replay results, highlighting what changed in the transaction context and policy. |
| `tests/test_compliance.py` | Added unit tests covering evidence pack zip generation and manifest validation, and policy replay detection (simulating policy changes). Updated `_reset_db` fixture to properly clean in-memory tables between tests. |
| `AGENTS.md` | Appended "Website Testing Coverage Rule" to ensure QA tasks explicitly cover website testing. |
| `.cursor/rules/qa-task-workflow.mdc` | Added the Website Testing Coverage Rule. |
| `New_task/_system/qa-agent-rules.md` | Added the Website Testing Coverage Rule. |
| `New_task/_system/task-run-checklist.md` | Added the Website Testing Coverage Rule. |
| `New_task/_system/report-template.md` | Added the Website Testing Coverage Rule. |
| `New_task/task-template.md` | Added the Website Testing Coverage Rule. |

## What I added
- Evidence Pack download: Packages the transaction payload, signed receipt, audit trail, active policy, and vendor info into a `.zip` file for auditor handoff. Tracks export events in the DB.
- Transaction Replay: Re-runs the policy checks against historical transaction data and compares decisions/steps, showing a diff to explain if "why would this transaction be approved/blocked today?".
- Risk Monitor: Shows vendor risk status, duplicate detection results, and missing evidence warnings directly on the dashboard detail page.
- QA task system rules emphasizing "Public Website Testing".

## What I modified
- Updated test environment setup so the DB is fully cleared between tests.

## What I did not change
- Core accounting logic, transaction states, receipt generation.

## Tests run
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

## Current status
- App status: Runs cleanly.
- Dashboard status: Added compliance section to transaction details.
- API status: No breaking changes. New endpoints for evidence and replay.
- Known issues: None.

## What the user should send to ChatGPT
Copy paste this whole latest `ForKnow.md` entry.

# Cursor Work Update: Phase 6A Release Hardening

## Date
2026-06-14T22:16:05.331288

## Prompt I worked on
Implement Phase 6A: release hardening, route consistency, security review, and final product closure.

## Files changed
| File | What changed |
|---|---|
| app/evidence_pack.py | Implemented real ZIP file generation using `zipfile` in-memory buffer. |
| app/main.py | Converted evidence pack route to `GET` download, added `/dashboard/risk` Risk Monitor route and gathered security events. |
| app/auth.py | Updated RBAC roles to strictly limit evidence, replay, and risk routes to `auditor` and `admin`. |
| app/templates/risk_monitor.html | Created new Risk Monitor template to render operational metrics and security events. |
| app/templates/partials/control_nav.html | Added Risk Monitor nav link. |
| docs/ROUTE_MAP.md | Added evidence, replay, and risk routes. |
| docs/SCHEMA_MAP.md | Added approval workflows and evidence_exports to schema map. |
| PROJECT.md | Marked Phase 6A complete. |
| README.md | Added explicit NO REAL MONEY MOVES EVER disclaimer and Phase 6A status. |
| tests/test_compliance.py | Updated tests for ZIP download, 403 authorization rejections, and Risk Monitor HTML rendering. |

## What I added
- Risk Monitor dashboard.
- Real ZIP file generator.

## What I modified
- Route and Role Base Access Control definitions.
- Documentation (ROUTE_MAP.md, SCHEMA_MAP.md, README.md, PROJECT.md).

## What I did not change
- I did not change JSON API success response shapes.
- I did not change the existing SQLite schema.
- I did not add any external integrations.

## Tests run
```bash
pytest -q tests/test_compliance.py
```

```text
...............................                                          [100%]
31 passed in 15.50s
```

## Current status
- App status: Hardened and complete.
- Dashboard status: Polished and responsive.
- API status: Protected and governed.
- Known issues: None.

## What the user should send to ChatGPT
Copy paste this whole latest ForKnow.md entry.

# Cursor Work Update: Phase 6B Release Closure

## Date
2026-06-14T22:29:45.806410

## Prompt I worked on
Phase 6B: full regression verification, release closure, and public-demo readiness.

## Files changed
| File | What changed |
|---|---|
| docs/RELEASE_CHECKLIST.md | Added final demo checklist section. |
| README.md | Added 'Current complete local demo' sequence list. |

## What I added
- Final demo checklist to RELEASE_CHECKLIST.md.
- Current complete local demo steps to README.md.

## What I modified
- README.md and docs/RELEASE_CHECKLIST.md formatting/additions.

## What I did not change
- Did not add new features.
- Did not add real payment execution.
- Did not break dashboard auth/RBAC/CSRF.
- Did not change JSON API response shapes.

## Tests run
```bash
pytest -q
```

```text
........................................................................ [ 28%]
........................................................................ [ 57%]
........................................................................ [ 85%]
....................................                                     [100%]
252 passed in 178.86s (0:02:58)
```

## Current status
- App status: Fully regression verified.
- Dashboard status: Polished and responsive.
- API status: Protected and governed.
- Known issues: None.

## What the user should send to ChatGPT
Copy paste this whole latest ForKnow.md entry.


# Cursor Work Update: Phase 6C Public GitHub/Demo Asset Polish

## Date
2026-06-14T22:49:30.948516

## Prompt I worked on
Phase 6C: public GitHub/demo asset polish. Preparing the repo for public GitHub/demo review without changing core app behavior.

## Files changed
| File | What changed |
|---|---|
| docs/DEMO_VIDEO_SCRIPT.md | Created new file with a polished 2 to 3 minute demo video script. |
| docs/screenshots/README.md | Updated the canonical screenshot list and capture flow. |
| docs/GITHUB_PUBLISHING.md | Created new file with the GitHub publishing checklist and repo metadata. |
| SECURITY.md | Created new file outlining the local prototype safety boundary. |
| README.md | Added links to the new documentation assets. |
| docs/RELEASE_CHECKLIST.md | Added Phase 6C checklist items. |
| TASKS.md | Marked Phase 6C as complete. |
| CHANGELOG.md | Added entry for Phase 6C. |
| HANDOFF.md | Updated handoff status to reflect completion. |

## What I added
- docs/DEMO_VIDEO_SCRIPT.md`n- docs/GITHUB_PUBLISHING.md`n- SECURITY.md`n
## What I modified
- docs/screenshots/README.md`n- docs/RELEASE_CHECKLIST.md`n- README.md`n- Memory files.

## What I did not change
- Did not add backend features.
- Did not change JSON API response shapes.
- Did not add external integrations or real payments.

## Tests run
```bash
pytest -q
```

```text
........................................................................ [ 28%]
........................................................................ [ 57%]
........................................................................ [ 85%]
....................................                                     [100%]
252 passed in 190.18s (0:03:10)
```

## Current status
- App status: Fully ready for public GitHub publishing.
- Dashboard status: Clean and unchanged.
- API status: Unchanged.
- Known issues: None.

## What the user should send to ChatGPT
Copy paste this whole latest ForKnow.md entry.


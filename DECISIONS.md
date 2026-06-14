# DECISIONS

Architectural and product decisions for ActionRail Finance. Each entry says **what** was decided and **why**, so a fresh model/chat can stay aligned without re-litigating settled questions.

Source of truth for product framing remains `PROJECT.md`. This file is the short, opinionated digest.

---

## D1. ActionRail starts with finance

**Decision:** The ActionRail platform's first wedge is finance operations.

**Why:**
- Finance actions are evidence-based (invoices, contracts, POs, ledger rows).
- Finance is policy-driven (thresholds, vendor approval, GL rules, approval chains).
- Finance is high-risk: wrong payments, duplicate invoices, bad journals create real damage.
- Outcomes are measurable: less manual review, faster close, fewer exceptions, better audit trail.
- Finance teams have willingness-to-pay for control, compliance, and reduced labor.

ActionRail is positioned as **the safe execution rail between AI finance agents and systems of record** — not an ERP, not a chatbot. Other verticals (travel, commerce, HR, legal, DevOps) come later, reusing the same transaction primitive.

---

## D2. MVP scope: invoice approval + duplicate detection

**Decision:** The MVP exercises exactly two flows — invoice approval and duplicate invoice detection.

**Why:**
- They are the smallest pair that proves the full lifecycle: `preflight -> decision -> approval -> execution -> receipt`.
- Both are concrete, demoable, and unambiguous to test.
- They surface every check we care about (vendor, duplicate, contract, amount, evidence, intent lock) without forcing us to ship integrations.
- They map directly to a YC-style demo: "block the duplicate, approve the legit large invoice, get a signed receipt".

Anything wider (journals, reconciliation, payments, vendor onboarding) is deferred to Phase 4+ in `PROJECT.md` section 20.

---

## D3. No real payment execution yet

**Decision:** Execution is simulated. The system never moves real money, never writes back to a real ERP, never hits real bank/payment rails.

**Why:**
- The MVP's job is to prove the **transaction rail**, not to be a payment processor.
- Real money movement requires production-grade auth, secret management, RBAC, audit logs, signed webhooks, and integration sandboxes — none of which are in scope.
- Safety boundary from `PROJECT.md` section 18: model outputs cannot directly mutate systems of record; approval and execution must be separate; receipts must be tamper-evident.
- Execution currently returns the demo string: `"Demo execution only. No real bank or ledger mutation performed."` Keep that boundary visible until sandbox integrations are an explicit task.

---

## D4. Dashboard is secondary to API/MCP

**Decision:** The primary surface is the API (and, later, MCP/SDK/CLI). The HTML dashboard exists for demo, debugging, and approval review — not as the product itself.

**Why:**
- The primary user is an AI agent, not a human clicking buttons.
- Agents need machine-readable responses: `allow`, `approval_required`, `blocked`, `needs_more_evidence`.
- Humans use the dashboard only for approvals, evidence review, audit trail, exceptions, and receipt lookup.
- Avoid the trap of overbuilding frontend before the workflow is stable. Polish the dashboard *after* the rail is solid — see `PROJECT.md` section 21 ("Cursor should not do these yet").

This also means: business logic stays in `app/policy.py` / `app/store.py`, not in route handlers or HTML templates.

---

## D5. Current tech stack

**Decision:** Python + FastAPI + Pydantic + SQLite + pytest, with a plain HTML dashboard. HMAC for receipt signatures.

**Why:**
- Smallest viable stack to prove the primitive on a single laptop.
- FastAPI gives us OpenAPI/Swagger for free, which doubles as agent-facing API docs.
- SQLite means zero infra to run the demo; schema lives in `app/store.py`.
- Pydantic models in `app/models.py` enforce the request/response shape for both humans and agents.
- pytest is already wired; tests live in `tests/test_policy.py`.

**Near-term planned additions** (not yet adopted, listed for direction only): PostgreSQL + SQLAlchemy/SQLModel + Alembic, Redis for locks/cache, MCP server package, JWT/API-key auth. Do not introduce these until a task explicitly calls for them.

**What we are *not* using yet (intentionally):** real OCR, real email ingestion, real ERP/bank connectors, JWT/RBAC, multi-tenant scoping, queues/event bus.

---

## D6. Dashboard adopts a neo-brutalist visual language via Jinja2 + static CSS

**Decision:** Render `/dashboard` (and any future HTML pages) through Jinja2 templates served by FastAPI, with a single hand-written CSS file at `app/static/neo.css` that centralizes neo-brutalist design tokens and utility classes. **No Tailwind, no Node toolchain, no JS framework.**

**Why:**
- The supplied design system (neo-brutalism: thick black borders, offset hard shadows, cream canvas, Space Grotesk 900, sticker rotations, color blocking, halftone texture) is stack-agnostic in spirit — only its examples are written in Tailwind. Vanilla CSS expresses every principle just as well.
- Jinja2 is the standard FastAPI templating partner and a single pure-Python dependency. It does not violate the spirit of D5 (Python/FastAPI/SQLite/Pydantic/pytest); it's a thin server-side templating layer, not a new runtime or build pipeline.
- Adding Tailwind/Node/Next.js would (a) introduce a frontend build pipeline, (b) require RBAC/auth choices for client-side rendering, and (c) violate D4's "dashboard is secondary, don't overbuild frontend before workflow is clear." All disproportionate to the dashboard's job.
- Centralizing tokens as CSS custom properties (`--neo-bg`, `--neo-accent`, `--shadow-md`, etc.) gives us the same maintainability win Tailwind would, with zero toolchain.

**Concrete additions:**
- `jinja2` added to `requirements.txt`.
- `app/templates/` — Jinja2 templates.
- `app/static/neo.css` — design tokens + utility classes.
- `Jinja2Templates` and `StaticFiles` mounts in `app/main.py`.

**What this does NOT change:**
- Backend logic (`app/policy.py`, `app/store.py`, `app/models.py`) is untouched.
- API endpoints and behaviors are unchanged. Only the HTML for `GET /dashboard` is replaced.
- Tests in `tests/test_policy.py` continue to pass with no edits.
- Agent-first framing (D4) is preserved: dashboard remains a review surface, not the product.

**Scope of first apply:** dashboard list view only — empty state + stats cards + styled transaction list. Detail page, approval buttons, execute button, receipt viewer, and preflight form remain in `TASKS.md` as follow-ups.

---

## D7. Phase 2A: local file upload with basic PDF text extraction

**Decision:** Add real invoice file upload (PDF, PNG, JPG) with local storage, SHA-256 hashing, basic regex-based field extraction from digital PDF text, and a manual-field override form. Upload files are stored under `data/uploads/` (gitignored). No external services, no cloud storage, no OCR.

**Why:**
- The demo can show a real user flow — "upload a PDF invoice, run preflight, get approval_required, approve, execute, receipt" — without involving real money or real systems.
- pypdf is pure Python, lightweight, and requires no system libraries. It works for digital (machine-generated) PDFs, which covers most real-world invoice formats.
- Image OCR (Tesseract / PaddleOCR / EasyOCR) is deferred to Phase 2B because it requires system-level dependencies, is unreliable without fine-tuning, and is not necessary to prove the transaction rail.
- The regex extraction is conservative: misses are safe, only high-confidence patterns are used, and the form always lets the user override any extracted field.
- `python-multipart` was already installed in the environment (required by FastAPI for file upload endpoints); it was added explicitly to `requirements.txt`.
- Local storage means no S3 credentials, no cloud costs, and no data leaving the user's machine in the MVP.

**What this does NOT include:**
- No OCR for images (Phase 2B).
- No connection to email inboxes (Phase 5).
- No file serving endpoint (files are evidence references only, not publicly viewable via the app).
- No real payment or bank integration.

---

## Decision log discipline

- New decisions get a new section (`D6`, `D7`, …) with **what** and **why**.
- Reversing a decision: do not delete the old entry — append a new one that supersedes it and explains the change.
- If a decision is contested mid-task, stop and surface the conflict before coding.

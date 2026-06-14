# ActionRail Finance — Demo Script (2–3 minutes)

Use this script when recording a demo or walking a reviewer through the MVP.

---

## One-line product explanation

**ActionRail Finance is a transaction runtime for finance AI agents** — it checks evidence, applies policy, gates approval, simulates execution, and produces signed receipts before any real system of record is touched.

---

## What problem it solves

AI finance agents need more than tool calls. Without a runtime layer:

- Duplicate invoices can slip through.
- Payments can execute without approval.
- Audit trails are missing.
- Two agents can conflict on the same invoice.

ActionRail turns every risky agent action into a **transaction** with a deterministic lifecycle and hard state guards.

---

## What the dashboard shows

Open: <http://127.0.0.1:8000/dashboard>

The dashboard is a **human review surface**, not the product. It shows:

- **Queue statistics** — current operational state (pending approval, blocked, executed).
- **RUN DEMO PREFLIGHT** — three one-click sample invoices.
- **Transaction queue** — Preflight Decision (historical policy outcome) vs Status (current lifecycle state).
- **Upload real invoice** — evidence intake with mandatory review before transaction creation.

Reset before recording:

```bash
python scripts/reset_demo_db.py
uvicorn app.main:app --reload
```

---

## Demo flow 1 — Approval-required invoice (~30 seconds)

1. Click **Approval Required Invoice**.
2. Point out: preflight decision = `approval_required`, status = `preflighted`, checks listed.
3. Click **Approve** → status becomes `approved`.
4. Click **Execute** → status becomes `executed` (simulated).
5. Note: blocked and missing-evidence demos are one click away from the dashboard.

**Say:** "The agent gets a machine-readable decision. Humans approve when required. Execution is a separate gated step."

---

## Demo flow 2 — Real invoice upload → OCR/review → transaction (~45 seconds)

1. Open **Upload real invoice** (`/dashboard/invoices/upload`).
2. Upload a sample image (e.g. `data/datasets/kaggle-invoices-sample/batch1-0001.jpg` after `prepare_invoice_samples.py`).
3. Review screen appears — OCR may prefill fields; user **must confirm** before a transaction is created.
4. If amount is missing, enter it manually (yellow "Manual review required" banner).
5. Click **Create ActionRail transaction**.
6. Transaction detail shows uploaded evidence, SHA-256, and "Reviewed before transaction" stamp.

**Say:** "OCR assists extraction. It does not auto-create finance transactions. A human confirms every field."

---

## Demo flow 3 — Approve → execute → signed receipt (~30 seconds)

1. From the uploaded (or demo) transaction: **Approve** → **Execute**.
2. Click **View Receipt**.
3. Show: receipt ID, HMAC-SHA256 signature, canonical signed JSON payload.
4. Point out the demo execution boundary line in the payload.

**Say:** "Every execution produces a tamper-evident receipt. The signature binds decision, evidence, approval, and execution timestamp."

---

## Demo flow 4 — Accounting sandbox writeback (~30 seconds)

1. Return to the executed transaction detail page.
2. Click **Create Accounting Sandbox Draft Bill**.
3. Writeback page shows: local sandbox safety note, draft bill JSON, audit packet JSON.
4. Return to transaction — **View Accounting Sandbox Writeback** replaces the create button.

**Say:** "This is a local sandbox adapter only. It proves the writeback boundary without touching QuickBooks, Xero, or any ledger."

---

## Safety boundary (say this explicitly)

> **Execution is simulated. No real money moves. No ERP, bank, or ledger mutation is performed.**

This is codified in every execution response and in the signed receipt payload. Real integrations require production auth, secret management, RBAC, and provider sandbox review.

---

## Closing pitch

ActionRail is an **execution-control layer for finance agents**, not another chatbot or invoice parser.

The MVP proves:

```text
preflight → decision → approval → simulated execution → signed receipt → local accounting sandbox writeback
```

The agent-facing API is the product. The dashboard exists so humans can review, approve, and demo.

---

## Further reading

- [`docs/PITCH.md`](PITCH.md) — concise pitch
- [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) — system design
- [`docs/SAFETY_BOUNDARY.md`](SAFETY_BOUNDARY.md) — what is and is not real
- [`docs/screenshots/README.md`](screenshots/README.md) — screenshot capture flow

# Screenshots

Place captured PNG screenshots in this directory.

**Screenshots are optional for tests** but **recommended before pinning the repo** for demos, README assets, and reviewer clarity.

## Canonical screenshot list (01–17)

```txt
01-login.png
02-dashboard-clean.png
03-invoice-upload.png
04-invoice-review.png
05-transaction-detail-preflight.png
06-approval-workflow.png
07-execution-ready.png
08-signed-receipt.png
09-accounting-writeback.png
10-evidence-pack.png
11-replay.png
12-risk-monitor.png
13-audit-log.png
14-admin-vendors.png
15-admin-contracts.png
16-admin-policies.png
17-admin-api-clients.png
```

Commit PNGs to this directory only if they contain safe demo data with no personal or real financial information.

## Recommended clean demo state

Always capture against a freshly reset database so the queue is empty before you start clicking. Otherwise the dashboard will include stale rows from earlier recording attempts.

```bash
# 1. Stop uvicorn if it's running.
python scripts/reset_demo_db.py
uvicorn app.main:app --reload
# 2. Open http://127.0.0.1:8000 at desktop width (≥ 1280px, zoom 90–100%).
```

For the real-upload demo, prepare sample images:

```bash
python scripts/prepare_invoice_samples.py --limit 10
```

## Capture flow

Run this exact sequence; each step maps to one screenshot.

| # | Filename | Route/Page | Login Role Needed | Required State Before Capture | What It Proves |
|---|---|---|---|---|---|
| 01 | `01-login.png` | `/login` | None (Logged out) | App started, user is logged out. | Secure RBAC authentication wall. |
| 02 | `02-dashboard-clean.png` | `/dashboard` | `controller` | Freshly reset DB. Queue is empty. | Core control plane overview. |
| 03 | `03-invoice-upload.png` | `/dashboard/invoices/upload` | `controller` | Upload form ready. | Ability to intake offline evidence. |
| 04 | `04-invoice-review.png` | `/dashboard/invoices/upload` (POST) | `controller` | Uploaded sample invoice. | OCR extraction and manual review step. |
| 05 | `05-transaction-detail-preflight.png` | `/dashboard/transactions/{id}` | `controller` | Transaction submitted, decision=`approval_required`. | Policy execution and preflight structural decision. |
| 06 | `06-approval-workflow.png` | `/dashboard/transactions/{id}` | `controller` | Still on the transaction detail. | Maker-checker controls (creator cannot approve). |
| 07 | `07-execution-ready.png` | `/dashboard/transactions/{id}` | `executor` | Transaction approved by an approver. | Approval gating and execution readiness. |
| 08 | `08-signed-receipt.png` | `/dashboard/transactions/{id}/receipt` | `executor` | Transaction executed. | Tamper-evident HMAC signed receipt generation. |
| 09 | `09-accounting-writeback.png` | `/dashboard/transactions/{id}/writeback/accounting-sandbox` | `executor` | Accounting draft generated. | Safe local sandbox writeback without external ERP mutation. |
| 10 | `10-evidence-pack.png` | `/dashboard/transactions/{id}` | `auditor` | Signed in as auditor. | Secure download for offline compliance packs. |
| 11 | `11-replay.png` | `/dashboard/transactions/{id}/replay` | `auditor` | Signed in as auditor. | Policy replay capabilities without state mutation. |
| 12 | `12-risk-monitor.png` | `/dashboard/risk` | `admin` | Some transactions and errors triggered. | Operational metrics and security event logging. |
| 13 | `13-audit-log.png` | `/dashboard/audit` | `admin` | Various lifecycle events triggered. | Immutable historical ledger. |
| 14 | `14-admin-vendors.png` | `/dashboard/admin/vendors` | `admin` | Seeded vendors exist. | Vendor onboarding and management. |
| 15 | `15-admin-contracts.png` | `/dashboard/admin/contracts` | `admin` | Seeded contracts exist. | Contract and evidence association. |
| 16 | `16-admin-policies.png` | `/dashboard/admin/policies` | `admin` | Policies visible. | Editable compliance thresholds. |
| 17 | `17-admin-api-clients.png` | `/dashboard/admin/api-clients` | `admin` | Default API clients exist. | Scoped API access and key security. |

## Tips for clean shots

* Hide any browser sidebars / dev tools.
* Use a dedicated demo profile so personal bookmarks and extensions don't appear.
* Capture the full page (a page-height screenshot, not just the viewport) so the table and receipt JSON aren't cut off.
* Keep transaction IDs visible — they're part of the proof that this is real ActionRail data, not a mockup.

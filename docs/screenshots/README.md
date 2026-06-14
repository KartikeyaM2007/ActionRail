# Screenshots

Place captured PNG screenshots in this directory.

## Recommended clean demo state

Always capture against a freshly reset database so the queue is empty before you start clicking. Otherwise the dashboard will include stale rows from earlier recording attempts.

```bash
# 1. Stop uvicorn if it's running.
python scripts/reset_demo_db.py
uvicorn app.main:app --reload
# 2. Open http://127.0.0.1:8000/dashboard at desktop width (≥ 1280px, zoom 90–100%).
```

For the real-upload demo (screenshots 08–11), also prepare sample images:

```bash
python scripts/prepare_invoice_samples.py --limit 10
# Files copied to: data/datasets/kaggle-invoices-sample/
# Use: data/datasets/kaggle-invoices-sample/batch1-0001.jpg
```

**Do not commit raw uploaded invoices unless they are safe sample images without personal/financial data.**

## Capture flow

Run this exact sequence; each step maps to one screenshot.

| # | Action | Filename |
|---|---|---|
| 01 | Open `/dashboard` immediately after the reset (queue is empty; the empty state lists the recommended demo order). | `01-dashboard-clean.png` |
| 02 | Click **Approval Required Invoice**. Capture the resulting transaction detail page (decision = `approval required`, status = `preflighted`, both **Approve** and **Reject** buttons visible). | `02-transaction-approval-required.png` |
| 03 | On that same transaction click **Approve**. Capture the page after the redirect (status = `approved`, **Execute** button now visible, **Reject** button gone). | `03-transaction-approved.png` |
| 04 | Click **Execute**. Capture the page (status = `executed`, **View Receipt** link visible, execution panel populated). | `04-transaction-executed.png` |
| 05 | Click **View Receipt**. Capture the receipt page showing receipt ID, full HMAC-SHA256 signature, and the signed canonical JSON payload. | `05-signed-receipt.png` |
| 06 | Return to `/dashboard`, click **Duplicate Invoice**, capture the resulting detail page (decision = `blocked`, no Execute button, `duplicate_invoice` check failed in the checks list). | `06-duplicate-blocked.png` |
| 07 | Return to `/dashboard`, click **Missing Evidence Invoice**, capture the detail page (decision = `needs more evidence`, `evidence_attached` check status `needs_evidence`, no Execute button). | `07-missing-evidence.png` |

## Naming convention

* Two-digit zero-padded prefix (`01`, `02`, …) so the files sort in capture order.
* All lowercase, hyphenated.
* `.png` only — vector text rendering stays crisp on retina displays.
* Keep originals at the captured resolution. Do not down-rez or compress before commit.

## Required filenames

```txt
01-dashboard-clean.png
02-transaction-approval-required.png
03-transaction-approved.png
04-transaction-executed.png
05-signed-receipt.png
06-duplicate-blocked.png
07-missing-evidence.png
08-upload-real-invoice.png
09-review-extracted-invoice.png
10-uploaded-invoice-transaction.png
11-uploaded-invoice-receipt.png
12-accounting-sandbox-writeback.png
13-executed-transaction-with-writeback.png
```

### Real-upload demo screenshots (08–11)

These four screenshots capture the two-step upload flow and are optional but recommended for demos that include real invoice images.

| # | Action | Filename |
|---|---|---|
| 08 | Open `/dashboard/invoices/upload`. The upload page should show the review-before-transaction copy. | `08-upload-real-invoice.png` |
| 09 | After uploading `data/datasets/kaggle-invoices-sample/batch1-0001.jpg`, the review screen appears. Capture it showing the yellow "Manual review required" banner (amount not extracted), pre-filled invoice_id and vendor, and the extraction notes list. | `09-review-extracted-invoice.png` |
| 10 | After entering the amount manually and submitting, the transaction detail page appears. Capture it showing the "Uploaded evidence" section with filename, SHA-256 short, extraction status, and "Reviewed before transaction: Yes — fields confirmed by user" stamp. | `10-uploaded-invoice-transaction.png` |
| 11 | After approve → execute, the receipt page shows the signed payload. The evidence reference `local://uploaded_documents/{id}` is part of the signed payload. | `11-uploaded-invoice-receipt.png` |

### Accounting sandbox writeback screenshots (12–13, optional)

| # | Action | Filename |
|---|---|---|
| 12 | After execute, capture the **transaction detail page before writeback**: state summary shows receipt available, **Next UI action** = `create_accounting_sandbox_writeback`, **Create Accounting Sandbox Draft Bill** button visible. | *(optional pre-writeback detail — use step 04 variant or real-upload post-execute detail)* |
| 12 | Click **Create Accounting Sandbox Draft Bill**. Capture the writeback page with the safety banner and writeback summary. Expand **draft bill JSON** (`<details>` open). | `12-accounting-sandbox-writeback.png` |
| 12b | Same writeback page with **audit packet JSON** expanded. | *(same file or second crop)* |
| 13 | Return to transaction detail **after writeback**: state summary mentions receipt + writeback, **Next UI action** = `view_accounting_sandbox_writeback`, only **View Accounting Sandbox Writeback** visible (no Create button). | `13-executed-transaction-with-writeback.png` |

**Capture notes:**

* Capture transaction detail **after execution, before writeback** — shows `create_accounting_sandbox_writeback` and Create button.
* Capture writeback page with **draft bill JSON expanded**.
* Capture writeback page with **audit packet JSON expanded** (can be same session as 12).
* Capture transaction detail **after writeback** — shows `view_accounting_sandbox_writeback` and View link only.

**Recommended full demo sequence including writeback:**

```txt
upload invoice → review fields → create transaction → approve → execute → view receipt
→ return to transaction → create accounting sandbox draft bill → view writeback page
```

## Tips for clean shots

* Hide any browser sidebars / dev tools.
* Use a dedicated demo profile so personal bookmarks and extensions don't appear.
* Capture the full page (a page-height screenshot, not just the viewport) so the table and receipt JSON aren't cut off.
* Keep transaction IDs visible — they're part of the proof that this is real ActionRail data, not a mockup.
* For the dashboard screenshots, scroll far enough up to show the stat cards (Total · Approval required · Needs evidence · Blocked · Executed) — they communicate the queue state at a glance.

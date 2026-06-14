# ActionRail Finance — Release Checklist

Run through this checklist before pushing a public GitHub release or recording a demo.

---

## 1. Tests

```bash
pytest -q
```

- [ ] All tests pass with zero failures.

---

## 2. Demo database reset

```bash
python scripts/reset_demo_db.py
```

- [ ] Database reset completed without errors.
- [ ] `data/uploads/` cleaned manually if needed (does not auto-delete).

---

## 3. OCR check (optional, only if using image upload demo)

```powershell
# Windows — add Tesseract to PATH for this session
$env:Path += ";C:\Program Files\Tesseract-OCR"

python scripts/check_ocr.py
```

- [ ] Pillow: OK
- [ ] pytesseract: OK
- [ ] Tesseract binary: OK
- [ ] Handshake: OK / Status: READY

If not using image upload, skip this.

---

## 4. OCR sample validation (optional)

```bash
python scripts/run_ocr_sample.py --limit 5
```

- [ ] 5/5 OCR status: ok
- [ ] invoice_id/vendor/date extracted on most samples
- [ ] amount extracted or "manual review required" shown clearly

---

## 5. Dashboard smoke test

Start the server:

```bash
uvicorn app.main:app --reload
```

- [ ] `/dashboard` redirects to `/login` when signed out.
- [ ] Login as `controller@example.local` / `controller123` succeeds.
- [ ] Dashboard loads with signed-in user visible in header.
- [ ] "RUN DEMO PREFLIGHT" buttons visible (controller).
- [ ] Stats cards visible (Total · Approval required · Needs evidence · Blocked · Executed).
- [ ] "Upload real invoice" button visible (controller/admin).
- [ ] Logout returns to `/login`.
- [ ] Login as `admin@example.local` → `/dashboard/admin` loads.
- [ ] Create vendor, contract, upload evidence, update policy threshold.
- [ ] Confirm admin actions appear in `/dashboard/audit`.

---

## 6. Core demo flow

Run from the dashboard:

- [ ] Click **Approval Required Invoice** → `decision=approval_required`, checks shown.
- [ ] Click **Approve** → status becomes `approved` (sign in as approver if using RBAC walkthrough).
- [ ] Click **Execute** → status becomes `executed`.
- [ ] Click **View Receipt** → signed HMAC-SHA256 receipt with canonical payload visible.
- [ ] Click **Create Accounting Sandbox Draft Bill** → writeback page shows safety banner, draft bill JSON, and audit packet JSON.
- [ ] Confirm writeback page shows `local://accounting_sandbox/...` references (not absolute file paths).
- [ ] Return to transaction → **View Accounting Sandbox Writeback** link visible (Create button gone).
- [ ] Return to dashboard → click **Duplicate Invoice** → `decision=blocked`, no Execute button.
- [ ] Return to dashboard → click **Missing Evidence Invoice** → `decision=needs_more_evidence`, no Execute button.

---

## 7. Real-upload flow (optional, recommended for demo)

- [ ] `python scripts/prepare_invoice_samples.py --limit 10` produces files in `data/datasets/kaggle-invoices-sample/`.
- [ ] Open `/dashboard/invoices/upload`.
- [ ] Upload `data/datasets/kaggle-invoices-sample/batch1-0001.jpg`.
- [ ] Review screen appears: yellow "Manual review required" banner if amount missing.
- [ ] Enter invoice amount manually.
- [ ] Click **Create ActionRail transaction**.
- [ ] Transaction detail shows "Uploaded evidence" section with filename, SHA-256 short, and "Reviewed before transaction: Yes — fields confirmed by user".
- [ ] Approve → Execute → View Receipt.
- [ ] Return to transaction → **Create Accounting Sandbox Draft Bill** → writeback page with safety banner, draft bill JSON, audit packet JSON.
- [ ] Receipt shows `local://uploaded_documents/{id}` evidence reference.

---

## 8. Git hygiene — nothing sensitive committed

```bash
git status
git diff --cached
```

```powershell
git status --ignored
git ls-files
```

**Ignored local files should include:** SQLite databases (`*.db`), `data/uploads/`, `data/datasets/` content, Kaggle credentials (`kaggle.json`, `.kaggle/`), `__pycache__/`, `.venv/`, generated accounting sandbox JSON (`data/accounting_sandbox/draft_bills/*`, `data/accounting_sandbox/audit_packets/*`), and `.env`.

- [ ] No `.db` files staged (`*.db` is in `.gitignore`).
- [ ] No `data/datasets/` content staged (`data/datasets/*` is in `.gitignore`).
- [ ] No `data/uploads/` content staged (`data/uploads/*` is in `.gitignore`).
- [ ] No generated sandbox writeback JSON staged (`data/accounting_sandbox/*` content gitignored).
- [ ] No `kaggle.json` staged (`kaggle/`, `kaggle.json`, `**/kaggle.json`, `.kaggle/` all in `.gitignore`).
- [ ] No `.env` staged.
- [ ] No local secrets staged.

---

## 9. README and docs review

- [ ] README says "Execution is simulated. No real money moves."
- [ ] README lists current MVP scope accurately.
- [ ] `docs/PITCH.md` does not claim real payments or production autonomy.
- [ ] `docs/OCR.md` describes OCR as optional.
- [ ] LICENSE file exists.

---

## 10. Screenshots

- [ ] Core demo screenshots captured (`01–07`): see [`docs/screenshots/README.md`](screenshots/README.md).
- [ ] Real-upload demo screenshots captured (`08–11`): see [`docs/screenshots/README.md`](screenshots/README.md).
- [ ] Optional accounting writeback screenshot (`12-accounting-sandbox-writeback.png`): see [`docs/screenshots/README.md`](screenshots/README.md).

Screenshots are not committed by default. Add them to a `docs/screenshots/` directory if including visual assets in the repo.

---

## 11. Push

```bash
git add .
git commit -m "chore: release prep — run through checklist"
git push
```

- [ ] CI/CD passes (if configured).
- [ ] GitHub repo is public or shared with intended reviewers.
- [ ] Demo URL is shared if deployed.

---

## 12. GitHub repo polish

- [ ] Repository description added (e.g. *Transaction runtime for finance AI agents — preflight, approval, simulated execution, signed receipts*).
- [ ] Topics added:

  ```text
  ai-agents
  finance-automation
  invoice-processing
  fastapi
  sqlite
  ocr
  audit-trail
  human-in-the-loop
  agent-safety
  transaction-runtime
  ```

- [ ] README renders correctly on GitHub (links to `docs/DEMO_SCRIPT.md`, `docs/ARCHITECTURE.md`, `docs/SAFETY_BOUNDARY.md`, `docs/PROJECT_COMPLETION.md`).
- [ ] LICENSE visible in repo root.
- [ ] `.gitignore` protecting DB, uploads, datasets, secrets, sandbox JSON.
- [ ] `pytest -q` passes locally.
- [ ] No local sensitive files staged (`git status`, `git ls-files`).
- [ ] Screenshots captured or intentionally deferred (see [`docs/screenshots/README.md`](screenshots/README.md)).
- [ ] GitHub repo pushed.
- [ ] Optional release tag created (e.g. `v0.1.0-mvp`).

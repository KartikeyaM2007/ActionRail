# OCR for Invoice Images

ActionRail Finance supports optional OCR for image invoices (PNG, JPG, JPEG).

**OCR is never required.** The app works without it. Without OCR, image uploads are stored as local evidence and you fill in the invoice fields manually. Digital PDFs always use pypdf text extraction and do not need OCR.

---

## How OCR works

When you upload an image invoice:

1. ActionRail calls `app.ocr.ocr_image_bytes()`.
2. If `pytesseract` and `Pillow` are installed and the Tesseract binary is on PATH, OCR runs and the extracted text is passed to the regex field extractor.
3. If OCR is unavailable or fails, the upload still works — you just fill in the fields manually.
4. OCR notes appear on the transaction detail page showing which engine was used and what happened.

---

## Installation

### Windows

Install the Python libraries:

```powershell
pip install pytesseract pillow
```

Install the Tesseract binary (required — pytesseract is just a Python wrapper):

- Download from: <https://github.com/UB-Mannheim/tesseract/wiki>
- Install to a known path (e.g. `C:\Program Files\Tesseract-OCR\tesseract.exe`).
- Add the Tesseract install directory to your `PATH` for the **current terminal session**:

```powershell
$env:Path += ";C:\Program Files\Tesseract-OCR"
```

Or add it **permanently** (run as administrator, then restart terminal):

```powershell
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files\Tesseract-OCR", [System.EnvironmentVariableTarget]::Machine)
```

Verify:

```powershell
tesseract --version
python scripts/check_ocr.py
```

### Linux / macOS

```bash
pip install pytesseract pillow
sudo apt-get install tesseract-ocr     # Debian/Ubuntu
# or
brew install tesseract                  # macOS
```

Verify:

```bash
tesseract --version
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

---

## Test OCR manually

1. Check OCR environment (new in Phase 2B-validation):

```powershell
python scripts/check_ocr.py
```

2. Prepare a small sample of invoice images from the Kaggle dataset:

```bash
python scripts/prepare_invoice_samples.py --limit 5
```

3. Run OCR on the samples and see extracted fields:

```bash
python scripts/run_ocr_sample.py --limit 5
python scripts/run_ocr_sample.py --limit 5 --save-report
```

4. Upload demo using the browser:

```text
1. Start the server: uvicorn app.main:app --reload
2. Open: http://127.0.0.1:8000/dashboard/invoices/upload
3. Upload one image from data/datasets/kaggle-invoices-sample/
4. Review the extracted fields on the review screen.
   - If "Manual review required" appears, enter the amount manually.
5. Confirm the fields and click "Create ActionRail transaction".
6. The transaction detail shows the uploaded evidence and extraction status.
7. Approve → Execute → View Receipt.
```

5. Start the server:

```bash
uvicorn app.main:app --reload
```

3. Open the upload page: <http://127.0.0.1:8000/dashboard/invoices/upload>

4. Upload one of the sample images from `data/datasets/kaggle-invoices-sample/`.

5. The transaction detail page will show extraction notes indicating:
   - `OCR engine: pytesseract` (if Tesseract is installed)
   - `OCR status: ok` (if text was extracted)
   - Any fields extracted via regex from the OCR text

---

## Dataset context

The Kaggle invoice dataset (`data/datasets/kaggle-invoices`) includes:

- **8,181 JPG invoice images** across 3 batches.
- **3 CSV annotation files** (`batch1_1.csv`, `batch1_2.csv`, `batch1_3.csv`).
- Each CSV row includes: `File Name`, `Json Data` (structured invoice JSON), `OCRed Text` (pre-computed OCR text).

The `OCRed Text` column is the same text Tesseract would produce. You can use it to validate ActionRail's regex field extractor **without running Tesseract locally**.

---

## Checking OCR status on the upload page

After an image upload, the transaction detail page shows an **Uploaded document** section with:

- `OCR engine: pytesseract` or `none`
- `OCR status: ok`, `not_available`, or `failed`
- Setup instructions if OCR is not available
- The first 400 characters of extracted text (if available)

---

## Limitations

- OCR quality depends heavily on image resolution and Tesseract's installed language packs.
- The regex field extractor is conservative — it prefers missing a field over guessing wrong. Fields not extracted with confidence are left blank for manual entry.
- This OCR layer is designed for **digital-quality invoice images**. Handwritten invoices, low-resolution scans, or non-Latin scripts may not extract well.
- Phase 2C (future): more capable document understanding (LayoutLM, Donut, etc.) is a separate concern and requires significantly more infrastructure.

---

## Not using OCR?

Image uploads always work without OCR. The trade-off:

| OCR installed | Result |
|---|---|
| Yes (pytesseract + Tesseract) | Fields auto-extracted from image; manual override still available |
| No | Upload stored as evidence; enter all fields manually in the form |

Both paths produce a valid ActionRail transaction with a local evidence reference.

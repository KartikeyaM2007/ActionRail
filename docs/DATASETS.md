# Invoice and Receipt Datasets

Reference list of publicly available datasets for testing and evaluating ActionRail's extraction pipeline (Phase 2B+). **None of these are downloaded automatically.**

## Security

- **Never commit `kaggle.json` or any credential file.** The `kaggle/` directory and all `kaggle.json` paths are in `.gitignore`.
- Never commit datasets. `data/datasets/` is in `.gitignore`.
- Verify each dataset's license before commercial or public use.

---

## Kaggle setup on Windows

Install the Kaggle package:

```powershell
pip install kaggle
```

Copy your credential to the official location (the script also auto-detects `kaggle/kaggle.json` locally, but the official location is safer):

```powershell
mkdir $env:USERPROFILE\.kaggle
copy .\kaggle\kaggle.json $env:USERPROFILE\.kaggle\kaggle.json
```

Verify setup:

```powershell
python scripts/download_sample_datasets.py --check-kaggle
```

Download the invoice image dataset:

```powershell
python scripts/download_sample_datasets.py --source kaggle-invoices --download
```

Or use the Kaggle CLI directly:

```powershell
kaggle datasets download -d osamahosamabdellatif/high-quality-invoice-images-for-ocr -p data/datasets/kaggle-invoices --unzip
```

Download with sample extraction (copies up to 20 files into `data/datasets/kaggle-invoices/sample/`):

```powershell
python scripts/download_sample_datasets.py --source kaggle-invoices --download --limit 20
```

## Kaggle setup on Linux / macOS

```bash
pip install kaggle
mkdir -p ~/.kaggle
cp kaggle/kaggle.json ~/.kaggle/kaggle.json
chmod 600 ~/.kaggle/kaggle.json
python scripts/download_sample_datasets.py --check-kaggle
python scripts/download_sample_datasets.py --source kaggle-invoices --download
```

---

## Common Kaggle errors

| Error | Cause | Fix |
|---|---|---|
| `403 Forbidden` | Dataset terms not accepted | Open the dataset URL in a browser while logged in to Kaggle and click "I Understand and Accept" |
| `401 Unauthorized` | Invalid or missing credentials | Check `kaggle.json` contains the correct `username` and `key`; copy it to `~/.kaggle/kaggle.json` |
| `Could not find kaggle.json` | Credential file not in the expected location | Run `python scripts/download_sample_datasets.py --check-kaggle` to see detected locations |
| `kaggle is not recognized` | Kaggle CLI not installed or not on PATH | Run `pip install kaggle`; restart your terminal |
| `Dataset terms not accepted` | Same as 403 — terms page must be accepted in browser | Log in to Kaggle and accept the dataset terms manually |
| `Dataset not found` | Dataset slug has changed | Visit the Kaggle URL and copy the correct dataset identifier |
| `ModuleNotFoundError: kaggle` | Kaggle package not installed in the active venv | `pip install kaggle` in the same environment as `uvicorn` |

---

## Important notes

- `data/datasets/` is in `.gitignore`. Datasets will not be committed.
- `kaggle/`, `kaggle.json`, `**/kaggle.json`, `.kaggle/` are all in `.gitignore`. Credentials will not be committed.
- Keep only small samples for local demo/testing.
- The full invoice image dataset (Kaggle) may be several hundred MB to a few GB. Use `--limit` to extract a sample.

---

## Datasets

### High Quality Invoice Images for OCR

| Field | Value |
|---|---|
| Source key | `kaggle-invoices` |
| Format | Invoice images (PNG/JPEG) |
| Use | Testing image upload + future OCR |
| Kaggle | <https://www.kaggle.com/datasets/osamahosamabdellatif/high-quality-invoice-images-for-ocr> |
| Hugging Face | <https://huggingface.co/datasets/Voxel51/high-quality-invoice-images-for-ocr> |
| Notes | Requires Kaggle login. Accept dataset terms in the browser before downloading. |

**Local dataset structure** (after download):

```text
data/datasets/kaggle-invoices/
  batch_1/
    batch_1/
      batch1_1/      (JPG images)
      batch1_2/      (JPG images)
      batch1_3/      (JPG images)
      batch1_1.csv   (annotations)
      batch1_2.csv   (annotations)
      batch1_3.csv   (annotations)
  batch_2/           (similar structure)
  batch_3/           (similar structure)
```

CSV columns: `File Name`, `Json Data` (structured invoice JSON), `OCRed Text` (pre-computed OCR text).

- **8,181 JPG images** total
- **3 CSV annotation files** with ground-truth invoice JSON + pre-computed OCR text

The `OCRed Text` column lets you test ActionRail's regex field extractor against real invoice text **without running Tesseract locally**.

Inspect the dataset:

```bash
python scripts/inspect_invoice_dataset.py
python scripts/prepare_invoice_samples.py --limit 20
```

### FATURA Invoice Dataset

| Field | Value |
|---|---|
| Format | Invoice images with ground-truth annotations |
| Use | Structured invoice field extraction |
| Paper | <https://arxiv.org/abs/2311.11856> |
| Zenodo | <https://zenodo.org/record/8261508> |
| Notes | Check Zenodo record license (typically CC-BY). |

### SROIE — Scanned Receipts OCR and Information Extraction

| Field | Value |
|---|---|
| Format | Scanned receipt images with key-value annotations |
| Use | Receipt parsing, OCR evaluation |
| Official challenge | <https://rrc.cvc.uab.es/?ch=13> |
| Kaggle mirror | <https://www.kaggle.com/datasets/urbikn/sroie-datasetv2> |
| Hugging Face mirror | <https://huggingface.co/datasets/rth/sroie-2019-v2> |
| Notes | Public challenge dataset. Check individual source licenses. |

### CORD — Consolidated Receipt Dataset

| Field | Value |
|---|---|
| Format | Receipt images with semantic entity labels |
| Use | End-to-end receipt parsing |
| GitHub | <https://github.com/clovaai/cord> |
| Hugging Face mirror | <https://huggingface.co/datasets/Voxel51/consolidated_receipt_dataset> |
| Notes | CLOVA AI open source. Review license in the GitHub repo. |

### FUNSD — Form Understanding in Noisy Scanned Documents

| Field | Value |
|---|---|
| Format | Noisy scanned forms with semantic annotations |
| Use | Structured document understanding, form fields |
| Official | <https://guillaumejaume.github.io/FUNSD/> |
| Hugging Face mirror | <https://huggingface.co/datasets/nielsr/funsd> |
| Notes | Research dataset. No login required. Review citation requirements. |

Download a sample (requires `pip install datasets`):

```bash
python scripts/download_sample_datasets.py --source funsd --limit 20
```

### RVL-CDIP — Document Classification

| Field | Value |
|---|---|
| Format | 400,000 grayscale document images, 16 classes (invoices, letters, forms, etc.) |
| Use | Document type classification (is this an invoice?) |
| Official | <https://adamharley.com/rvl-cdip/> |
| Hugging Face | <https://huggingface.co/datasets/aharley/rvl_cdip> |
| Notes | **Large dataset (~40 GB).** Never auto-downloaded. Manual download only. |

---

## Quick reference — all download commands

```bash
# Check Kaggle credentials
python scripts/download_sample_datasets.py --check-kaggle

# See all dataset links
python scripts/download_sample_datasets.py

# Kaggle invoice images — print instructions only
python scripts/download_sample_datasets.py --source kaggle-invoices --instructions

# Kaggle invoice images — download + unzip
python scripts/download_sample_datasets.py --source kaggle-invoices --download

# Kaggle invoice images — download and extract 20 sample files
python scripts/download_sample_datasets.py --source kaggle-invoices --download --limit 20

# FUNSD sample (no login required)
python scripts/download_sample_datasets.py --source funsd --limit 20
```

---

Full downloads are never automatic and never required for the ActionRail demo. The existing demo payloads in `examples/` are sufficient for all current tests.

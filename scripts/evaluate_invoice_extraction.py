"""
ActionRail Finance — invoice field extraction evaluator.

Reads OCR text from the Kaggle invoice CSV annotations and runs
extract_fields_from_text() without requiring images or Tesseract.
Reports extraction coverage across invoice_id, vendor, date, amount, currency.

Usage:
    python scripts/evaluate_invoice_extraction.py
    python scripts/evaluate_invoice_extraction.py --limit 50
    python scripts/evaluate_invoice_extraction.py --limit 100 --csv-path path/to/file.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_CSV = (
    _REPO_ROOT
    / "data" / "datasets" / "kaggle-invoices"
    / "batch_1" / "batch_1" / "batch1_1.csv"
)

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _pct(n: int, total: int) -> str:
    return f"{n}/{total} ({100*n//total if total else 0}%)"


def evaluate(csv_path: Path, limit: int) -> None:
    print("\nActionRail Finance — Extraction Evaluator (CSV-only, no OCR needed)")
    print("=" * 60)
    print(f"  CSV  : {csv_path}")
    print(f"  Limit: {limit}")
    print()

    if not csv_path.exists():
        print(f"  ERROR: CSV not found: {csv_path}")
        print()
        print("  Download the dataset first:")
        print(
            "    python scripts/download_sample_datasets.py"
            " --source kaggle-invoices --download"
        )
        return

    from app.extraction import extract_fields_from_text

    rows_evaluated = 0
    counts = {
        "invoice_id": 0,
        "vendor": 0,
        "invoice_date": 0,
        "amount": 0,
        "currency": 0,
    }
    amount_missing_examples: list[dict] = []

    with csv_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if rows_evaluated >= limit:
                break
            ocr_text = row.get("OCRed Text", "").strip()
            if not ocr_text:
                continue

            result = extract_fields_from_text(ocr_text)
            fields = result.get("fields", {})
            notes  = result.get("notes", [])

            for field in counts:
                if fields.get(field):
                    counts[field] += 1

            if not fields.get("amount") and len(amount_missing_examples) < 3:
                # Pull ground-truth amount from Json Data if available
                gt_amount = ""
                try:
                    gt = json.loads(row.get("Json Data", "{}"))
                    gt_amount = gt.get("subtotal", {}).get("total", "")
                except Exception:
                    pass
                amount_missing_examples.append({
                    "ocr_preview": ocr_text[:120],
                    "gt_amount": gt_amount,
                    "notes": [n for n in notes if "amount" in n.lower() or "manual" in n.lower()],
                })

            rows_evaluated += 1

    if rows_evaluated == 0:
        print("  No rows with OCR text found in the CSV.")
        return

    print(f"  Rows evaluated: {rows_evaluated}")
    print()
    print("  Extraction coverage:")
    for field, n in counts.items():
        print(f"    {field:15s}: {_pct(n, rows_evaluated)}")

    print()
    print(f"  Amount missing on {rows_evaluated - counts['amount']} rows.")
    if amount_missing_examples:
        print()
        print("  Examples where amount was skipped:")
        for i, ex in enumerate(amount_missing_examples, 1):
            print(f"    [{i}] OCR: {ex['ocr_preview']!r}")
            print(f"         GT amount: {ex['gt_amount']!r}")
            for note in ex["notes"]:
                print(f"         Note: {note}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate field extraction coverage against Kaggle CSV OCR text"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Number of CSV rows to evaluate (default: 50)",
    )
    parser.add_argument(
        "--csv-path",
        default=str(_DEFAULT_CSV),
        help=f"Path to the annotation CSV file (default: {_DEFAULT_CSV})",
    )
    args = parser.parse_args()
    evaluate(Path(args.csv_path), args.limit)


if __name__ == "__main__":
    main()

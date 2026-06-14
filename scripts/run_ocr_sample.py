"""
ActionRail Finance — OCR sample runner.

Runs OCR on a small number of images from the prepared sample folder and
prints a summary of extraction results. Optionally saves a JSON report.

Usage:
    python scripts/run_ocr_sample.py
    python scripts/run_ocr_sample.py --limit 5
    python scripts/run_ocr_sample.py --limit 5 --save-report
    python scripts/run_ocr_sample.py --source data/datasets/kaggle-invoices-sample --limit 3
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_SOURCE = _REPO_ROOT / "data" / "datasets" / "kaggle-invoices-sample"
_REPORT_DIR = _REPO_ROOT / "data" / "datasets" / "ocr_reports"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".webp"}


def run_on_folder(source: Path, limit: int, save_report: bool) -> None:
    print("\nActionRail Finance — OCR Sample Runner")
    print("=" * 60)
    print(f"  Source  : {source}")
    print(f"  Limit   : {limit}")
    print()

    if not source.exists():
        print(f"  ERROR: Sample folder does not exist: {source}")
        print()
        print("  Create it first:")
        print("    python scripts/prepare_invoice_samples.py --limit 20")
        return

    images = sorted(
        f for f in source.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    )

    if not images:
        print(f"  No image files found in {source}.")
        print("  Run: python scripts/prepare_invoice_samples.py --limit 20")
        return

    selected = images[:limit]
    print(f"  Found {len(images)} image(s), testing {len(selected)}.\n")

    # Import the ActionRail OCR and extraction modules.
    # Add repo root to path so we can import from app/.
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))

    from app.ocr import ocr_image_bytes
    from app.extraction import extract_fields_from_text

    results = []
    ok_count = 0
    amount_extracted = 0
    amount_missing = 0
    currency_extracted = 0
    manual_review_required = 0

    for img_path in selected:
        print(f"  [{img_path.name}]")
        file_bytes = img_path.read_bytes()

        ocr_result = ocr_image_bytes(file_bytes, filename=img_path.name)
        status = ocr_result["status"]
        engine = ocr_result["engine"]
        text = ocr_result.get("text") or ""
        ocr_notes = ocr_result.get("notes", [])

        print(f"    OCR status : {status}")
        print(f"    OCR engine : {engine}")
        print(f"    Text length: {len(text)} chars")

        extraction = {"fields": {}, "notes": []}
        if status == "ok" and text:
            ok_count += 1
            print(f"    Text (first 300 chars):")
            preview = text[:300].replace("\n", " | ")
            # Sanitise for Windows cp1252 terminal
            preview = preview.encode("ascii", errors="replace").decode("ascii")
            print(f"      {preview}")
            extraction = extract_fields_from_text(text)
        elif ocr_notes:
            for note in ocr_notes[:2]:
                print(f"    Note: {note}")

        extracted_fields = extraction.get("fields", {})
        extraction_notes = extraction.get("notes", [])

        if extracted_fields:
            field_count = len(extracted_fields)
            print(f"    Extracted fields: {field_count}")
            for k, v in extracted_fields.items():
                print(f"      {k}: {v}")
        else:
            field_count = 0
            print(f"    Extracted fields: none")

        # Track per-field stats
        if "amount" in extracted_fields:
            amount_extracted += 1
        else:
            amount_missing += 1
            if any("Manual review required" in n for n in extraction_notes):
                manual_review_required += 1
        if "currency" in extracted_fields:
            currency_extracted += 1

        # Print the first 3 extraction notes
        for note in extraction_notes[:3]:
            print(f"    Note: {note}")

        print()

        results.append({
            "filename": img_path.name,
            "ocr_status": status,
            "ocr_engine": engine,
            "text_length": len(text),
            "text_preview": text[:300] if text else None,
            "ocr_notes": ocr_notes,
            "extracted_fields": extracted_fields,
            "extraction_notes": extraction_notes,
        })    # Summary
    print("-" * 60)
    print(f"  Tested                  : {len(selected)}")
    print(f"  OCR ok                  : {ok_count}")
    print(f"  Amount extracted        : {amount_extracted}")
    print(f"  Amount missing/skipped  : {amount_missing}")
    print(f"  Currency extracted      : {currency_extracted}")
    print(f"  Manual review required  : {manual_review_required}")
    print()

    if ok_count == 0:
        print("  No OCR succeeded. Common causes:")
        print("    - Tesseract not on PATH  →  $env:Path += \";C:\\Program Files\\Tesseract-OCR\"")
        print("    - pytesseract not installed  →  pip install pytesseract pillow")
        print("    - Run: python scripts/check_ocr.py")

    # Optionally save report
    if save_report:
        _REPORT_DIR.mkdir(parents=True, exist_ok=True)
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": str(source),
            "tested": len(selected),
            "ocr_ok": ok_count,
            "total_fields_extracted": field_count,
            "results": results,
        }
        report_path = _REPORT_DIR / "latest_ocr_report.json"
        report_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"  Report saved: {report_path}")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run OCR on invoice image samples and print extraction results"
    )
    parser.add_argument(
        "--source",
        default=str(_DEFAULT_SOURCE),
        help=f"Image source directory (default: {_DEFAULT_SOURCE})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of images to test (default: 5)",
    )
    parser.add_argument(
        "--save-report",
        action="store_true",
        help="Save JSON report to data/datasets/ocr_reports/latest_ocr_report.json",
    )
    args = parser.parse_args()
    run_on_folder(Path(args.source), args.limit, args.save_report)


if __name__ == "__main__":
    main()

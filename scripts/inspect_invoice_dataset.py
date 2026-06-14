"""
ActionRail Finance — Kaggle invoice dataset inspector.

Prints the structure and file counts of data/datasets/kaggle-invoices
without loading images into memory.

Usage:
    python scripts/inspect_invoice_dataset.py
    python scripts/inspect_invoice_dataset.py --path data/datasets/kaggle-invoices
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DATASET = _REPO_ROOT / "data" / "datasets" / "kaggle-invoices"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".webp"}


def inspect(dataset_path: Path) -> None:
    print("\nActionRail Finance — Invoice Dataset Inspector")
    print("=" * 60)
    print(f"  Path : {dataset_path}")

    if not dataset_path.exists():
        print()
        print("  ERROR: Dataset path does not exist.")
        print()
        print("  Download the dataset first:")
        print(
            "    python scripts/download_sample_datasets.py"
            " --source kaggle-invoices --download"
        )
        return

    # --- Count files by extension ------------------------------------------
    all_files = [f for f in dataset_path.rglob("*") if f.is_file()]
    ext_counts = Counter(f.suffix.lower() for f in all_files)

    total = len(all_files)
    image_files = [f for f in all_files if f.suffix.lower() in IMAGE_EXTENSIONS]
    csv_files = [f for f in all_files if f.suffix.lower() == ".csv"]

    print(f"\n  Total files       : {total}")
    print(f"  Image files       : {len(image_files)}")
    print(f"  Annotation CSVs   : {len(csv_files)}")
    print()
    print("  File type breakdown:")
    for ext, count in ext_counts.most_common():
        print(f"    {ext or '(no ext)':12s}: {count}")

    # --- Folder layout --------------------------------------------------------
    subdirs = sorted(set(
        str(f.parent.relative_to(dataset_path)) for f in all_files
        if str(f.parent.relative_to(dataset_path)) != "."
    ))
    print(f"\n  Subdirectories    : {len(subdirs)}")
    for d in subdirs[:15]:
        print(f"    {d}")
    if len(subdirs) > 15:
        print(f"    ... ({len(subdirs) - 15} more)")

    # --- First 10 images ------------------------------------------------------
    print(f"\n  First 10 image files:")
    for img in sorted(image_files)[:10]:
        print(f"    {img.relative_to(dataset_path)}")

    # --- Annotation CSV summary -----------------------------------------------
    print(f"\n  Annotation CSV files:")
    for csv_path in sorted(csv_files):
        print(f"    {csv_path.relative_to(dataset_path)}")
        try:
            with csv_path.open(encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            print(f"      Columns : {', '.join(reader.fieldnames or [])}")
            print(f"      Rows    : {len(rows)}")
            # Peek at the JSON structure in 'Json Data' if present
            if rows and "Json Data" in rows[0]:
                try:
                    sample_json = json.loads(rows[0]["Json Data"])
                    top_keys = list(sample_json.keys())[:5]
                    print(f"      Json keys (sample): {top_keys}")
                except json.JSONDecodeError:
                    pass
            if rows and "OCRed Text" in rows[0]:
                ocr_text_sample = rows[0]["OCRed Text"][:80].replace("\n", " ")
                print(f"      OCRed Text sample : {ocr_text_sample!r}")
        except Exception as exc:
            print(f"      (could not read CSV: {exc})")

    # --- Recommendations ------------------------------------------------------
    print()
    print("  Recommended next commands:")
    print(
        "    python scripts/prepare_invoice_samples.py --limit 20"
    )
    print(
        "    # then upload a file from data/datasets/kaggle-invoices-sample/ via the dashboard"
    )
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect the local Kaggle invoice dataset")
    parser.add_argument(
        "--path",
        default=str(_DEFAULT_DATASET),
        help=f"Dataset directory path (default: {_DEFAULT_DATASET})",
    )
    args = parser.parse_args()
    inspect(Path(args.path))


if __name__ == "__main__":
    main()

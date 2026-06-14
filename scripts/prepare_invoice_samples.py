"""
ActionRail Finance — invoice sample preparation script.

Copies a small number of invoice images from the downloaded Kaggle dataset
into a clean sample folder for OCR testing and manual upload experiments.

Usage:
    python scripts/prepare_invoice_samples.py
    python scripts/prepare_invoice_samples.py --limit 20
    python scripts/prepare_invoice_samples.py --source data/datasets/kaggle-invoices --limit 10

Output folder: data/datasets/kaggle-invoices-sample/

Rules:
- Only copies image files.
- Does not modify the source dataset.
- Does not commit sample files (see .gitignore).
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SOURCE_DEFAULT = _REPO_ROOT / "data" / "datasets" / "kaggle-invoices"
_DEST_DEFAULT = _REPO_ROOT / "data" / "datasets" / "kaggle-invoices-sample"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".webp"}


def prepare_samples(source: Path, dest: Path, limit: int) -> int:
    """
    Copy at most `limit` image files from `source` to `dest`.
    Returns the number of files copied.
    """
    if not source.exists():
        print()
        print(f"ERROR: Source dataset path does not exist: {source}")
        print()
        print("Download the dataset first:")
        print(
            "  python scripts/download_sample_datasets.py"
            " --source kaggle-invoices --download"
        )
        return 0

    dest.mkdir(parents=True, exist_ok=True)

    image_files = sorted(
        f for f in source.rglob("*")
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    )

    if not image_files:
        print(f"No image files found under {source}.")
        return 0

    selected = image_files[:limit]
    print(f"\nActionRail Finance — Invoice Sample Preparation")
    print("=" * 60)
    print(f"  Source      : {source}")
    print(f"  Destination : {dest}")
    print(f"  Images found: {len(image_files)}")
    print(f"  Copying     : {len(selected)} (limit={limit})")
    print()

    copied = 0
    for src_path in selected:
        dest_path = dest / src_path.name
        if dest_path.exists():
            print(f"  SKIP (exists): {src_path.name}")
            continue
        shutil.copy2(src_path, dest_path)
        print(f"  Copied: {src_path.name}")
        copied += 1

    print()
    print(f"Done. {copied} new file(s) copied to {dest}")
    print("Reminder: never commit data/datasets/ to git.")
    print()
    print("Next: upload a file from this folder via the dashboard:")
    print("  http://127.0.0.1:8000/dashboard/invoices/upload")
    return copied


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy invoice image samples for OCR testing"
    )
    parser.add_argument(
        "--source",
        default=str(_SOURCE_DEFAULT),
        help=f"Source dataset directory (default: {_SOURCE_DEFAULT})",
    )
    parser.add_argument(
        "--dest",
        default=str(_DEST_DEFAULT),
        help=f"Destination sample directory (default: {_DEST_DEFAULT})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of images to copy (default: 20)",
    )
    args = parser.parse_args()
    prepare_samples(Path(args.source), Path(args.dest), args.limit)


if __name__ == "__main__":
    main()

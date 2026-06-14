"""
ActionRail Finance — dataset download helper.

Prints links and instructions by default. Downloading is always opt-in.

Usage:
    python scripts/download_sample_datasets.py
    python scripts/download_sample_datasets.py --check-kaggle
    python scripts/download_sample_datasets.py --source kaggle-invoices --instructions
    python scripts/download_sample_datasets.py --source kaggle-invoices --download
    python scripts/download_sample_datasets.py --source kaggle-invoices --download --limit 20
    python scripts/download_sample_datasets.py --source funsd --limit 20

Security:
    Never print Kaggle credential file contents.
    Never commit kaggle.json or any credential file.
    The kaggle/ directory is in .gitignore.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DATA_DIR = _REPO_ROOT / "data" / "datasets"

# ---------------------------------------------------------------------------
# Kaggle dataset identifiers
# ---------------------------------------------------------------------------

KAGGLE_INVOICE_DATASET = "osamahosamabdellatif/high-quality-invoice-images-for-ocr"
KAGGLE_INVOICE_DEST = _DATA_DIR / "kaggle-invoices"

# ---------------------------------------------------------------------------
# Dataset reference table
# ---------------------------------------------------------------------------

DATASET_LINKS: dict[str, dict] = {
    "high_quality_invoices": {
        "description": "High Quality Invoice Images for OCR",
        "kaggle": f"https://www.kaggle.com/datasets/{KAGGLE_INVOICE_DATASET}",
        "huggingface": "https://huggingface.co/datasets/Voxel51/high-quality-invoice-images-for-ocr",
        "notes": "Requires Kaggle login. Review Kaggle dataset license.",
        "auto_download": False,
    },
    "kaggle-invoices": {
        "description": "High Quality Invoice Images for OCR (via Kaggle CLI)",
        "kaggle": f"https://www.kaggle.com/datasets/{KAGGLE_INVOICE_DATASET}",
        "notes": "Requires kaggle package + accepted dataset terms. See --check-kaggle.",
        "auto_download": True,
    },
    "fatura": {
        "description": "FATURA Invoice Dataset",
        "zenodo": "https://zenodo.org/record/8261508",
        "paper": "https://arxiv.org/abs/2311.11856",
        "notes": "Check Zenodo license (typically CC-BY).",
        "auto_download": False,
    },
    "sroie": {
        "description": "SROIE — Scanned Receipts OCR and Information Extraction",
        "kaggle": "https://www.kaggle.com/datasets/urbikn/sroie-datasetv2",
        "huggingface": "https://huggingface.co/datasets/rth/sroie-2019-v2",
        "notes": "Public challenge dataset. Check license.",
        "auto_download": False,
    },
    "cord": {
        "description": "CORD — Consolidated Receipt Dataset",
        "github": "https://github.com/clovaai/cord",
        "huggingface": "https://huggingface.co/datasets/Voxel51/consolidated_receipt_dataset",
        "notes": "CLOVA AI open source. Review GitHub license.",
        "auto_download": False,
    },
    "funsd": {
        "description": "FUNSD — Form Understanding in Noisy Scanned Documents",
        "official": "https://guillaumejaume.github.io/FUNSD/",
        "huggingface": "https://huggingface.co/datasets/nielsr/funsd",
        "notes": "Research dataset. Review citation requirements.",
        "auto_download": True,
    },
    "rvl_cdip": {
        "description": "RVL-CDIP — Document Classification (400k images, ~40 GB)",
        "official": "https://adamharley.com/rvl-cdip/",
        "huggingface": "https://huggingface.co/datasets/aharley/rvl_cdip",
        "notes": "LARGE (~40 GB). Never auto-downloaded.",
        "auto_download": False,
    },
}

# ---------------------------------------------------------------------------
# Kaggle credential detection
# ---------------------------------------------------------------------------

class KaggleCredStatus(NamedTuple):
    found: bool
    path: Path | None
    is_project_local: bool
    warning: str | None


def detect_kaggle_credentials() -> KaggleCredStatus:
    """
    Find kaggle.json from the standard locations, in priority order:
      1. %USERPROFILE%\\.kaggle\\kaggle.json  (Windows official)
      2. ~/.kaggle/kaggle.json               (Linux/macOS official)
      3. kaggle/kaggle.json                  (project-local fallback)

    Never prints file contents.
    """
    # 1. Windows official
    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        win_path = Path(userprofile) / ".kaggle" / "kaggle.json"
        if win_path.exists():
            return KaggleCredStatus(
                found=True, path=win_path, is_project_local=False, warning=None
            )

    # 2. Linux/macOS official
    home_path = Path.home() / ".kaggle" / "kaggle.json"
    if home_path.exists():
        return KaggleCredStatus(
            found=True, path=home_path, is_project_local=False, warning=None
        )

    # 3. Project-local fallback
    local_path = _REPO_ROOT / "kaggle" / "kaggle.json"
    if local_path.exists():
        return KaggleCredStatus(
            found=True,
            path=local_path,
            is_project_local=True,
            warning=(
                "Using project-local kaggle/kaggle.json. "
                "This is okay for local development, but it must never be committed. "
                "See .gitignore — the kaggle/ directory is excluded."
            ),
        )

    return KaggleCredStatus(found=False, path=None, is_project_local=False, warning=None)


def kaggle_package_available() -> bool:
    """Return True if the kaggle Python package or CLI is usable."""
    try:
        import importlib.util
        return importlib.util.find_spec("kaggle") is not None
    except Exception:
        pass
    return shutil.which("kaggle") is not None


# ---------------------------------------------------------------------------
# Credential-aware environment setup
# ---------------------------------------------------------------------------

def configure_kaggle_env(cred: KaggleCredStatus) -> None:
    """
    If using a project-local credential, point KAGGLE_CONFIG_DIR at it.
    Never modify environment when using the official location.
    """
    if cred.is_project_local and cred.path is not None:
        os.environ["KAGGLE_CONFIG_DIR"] = str(cred.path.parent)


# ---------------------------------------------------------------------------
# --check-kaggle
# ---------------------------------------------------------------------------

def check_kaggle() -> None:
    print("\nActionRail Finance — Kaggle credential check")
    print("=" * 60)

    # Package
    has_pkg = kaggle_package_available()
    print(f"  Kaggle package installed : {'YES' if has_pkg else 'NO'}")
    if not has_pkg:
        print()
        print("  Install with:")
        print("    pip install kaggle")
        print()

    # Credentials
    cred = detect_kaggle_credentials()
    print(f"  Credentials found        : {'YES' if cred.found else 'NO'}")
    if cred.path:
        # Print path but never contents
        print(f"  Credential path          : {cred.path}")
        print(f"  Inside repo              : {'YES — see warning below' if cred.is_project_local else 'NO'}")
    if cred.warning:
        print()
        print(f"  WARNING: {cred.warning}")

    if not cred.found:
        print()
        print("  Credentials not found. To set them up:")
        print()
        print("  Windows (PowerShell):")
        print("    mkdir $env:USERPROFILE\\.kaggle")
        print("    copy .\\kaggle\\kaggle.json $env:USERPROFILE\\.kaggle\\kaggle.json")
        print()
        print("  Linux / macOS:")
        print("    mkdir -p ~/.kaggle")
        print("    cp kaggle/kaggle.json ~/.kaggle/kaggle.json")
        print("    chmod 600 ~/.kaggle/kaggle.json")

    # Dataset access verdict
    print()
    can_attempt = has_pkg and cred.found
    if can_attempt:
        print("  Dataset download: READY")
        print(f"  Dataset: {KAGGLE_INVOICE_DATASET}")
        print()
        print("  Run:")
        print("    python scripts/download_sample_datasets.py --source kaggle-invoices --download")
    else:
        missing = []
        if not has_pkg:
            missing.append("kaggle package (pip install kaggle)")
        if not cred.found:
            missing.append("kaggle credentials (see setup above)")
        print(f"  Dataset download: NOT READY — missing: {', '.join(missing)}")

    print()


# ---------------------------------------------------------------------------
# --source kaggle-invoices --instructions
# ---------------------------------------------------------------------------

def print_kaggle_instructions() -> None:
    print("\nKaggle invoice dataset — manual download command")
    print("=" * 60)
    print(f"\n  Dataset: {KAGGLE_INVOICE_DATASET}")
    print(f"  URL    : https://www.kaggle.com/datasets/{KAGGLE_INVOICE_DATASET}")
    print()
    print("  Requires: pip install kaggle   and   kaggle.json credentials")
    print()
    print("  Direct CLI command:")
    print(
        f"    kaggle datasets download"
        f" -d {KAGGLE_INVOICE_DATASET}"
        f" -p {KAGGLE_INVOICE_DEST}"
        f" --unzip"
    )
    print()
    print("  Via this script:")
    print(
        "    python scripts/download_sample_datasets.py"
        " --source kaggle-invoices --download"
    )
    print()
    print("  Kaggle may require accepting dataset terms in the browser first:")
    print(f"    https://www.kaggle.com/datasets/{KAGGLE_INVOICE_DATASET}")
    print()


# ---------------------------------------------------------------------------
# --source kaggle-invoices --download
# ---------------------------------------------------------------------------

def download_kaggle_invoices(limit: int | None = None) -> None:
    """
    Download the Kaggle invoice dataset using the kaggle CLI via subprocess.
    Sets KAGGLE_CONFIG_DIR if using a project-local credential file.
    """
    print("\nActionRail Finance — Kaggle invoice dataset download")
    print("=" * 60)

    # Pre-flight checks
    if not kaggle_package_available():
        print("\nERROR: kaggle package is not installed.")
        print("  Install with:  pip install kaggle")
        print("  Then retry.")
        sys.exit(1)

    cred = detect_kaggle_credentials()
    if not cred.found:
        print("\nERROR: kaggle.json credentials not found.")
        print("  Run:  python scripts/download_sample_datasets.py --check-kaggle")
        print("  for setup instructions.")
        sys.exit(1)

    if cred.warning:
        print(f"\n  WARNING: {cred.warning}")

    # Point kaggle at the right credential location
    configure_kaggle_env(cred)

    dest = KAGGLE_INVOICE_DEST
    dest.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "kaggle",
        "datasets", "download",
        "-d", KAGGLE_INVOICE_DATASET,
        "-p", str(dest),
        "--unzip",
    ]

    print(f"\n  Downloading to: {dest}")
    print(f"  Dataset       : {KAGGLE_INVOICE_DATASET}")
    print(f"  Command       : {' '.join(cmd)}")
    print()
    print("  This may take a few minutes depending on dataset size.")
    print("  If you see a 403/401, you may need to accept dataset terms at:")
    print(f"    https://www.kaggle.com/datasets/{KAGGLE_INVOICE_DATASET}")
    print()

    try:
        result = subprocess.run(cmd, check=False)
    except FileNotFoundError:
        print("ERROR: Could not run the kaggle CLI.")
        print("  Make sure 'pip install kaggle' has been run in the active environment.")
        sys.exit(1)

    if result.returncode != 0:
        print()
        print(f"ERROR: kaggle exited with code {result.returncode}.")
        print()
        print("Common causes:")
        print("  403 Forbidden    : Accept dataset terms at the Kaggle URL above.")
        print("  401 Unauthorized : Check that kaggle.json contains valid credentials.")
        print("  404 Not Found    : Dataset identifier may have changed.")
        print()
        print("See docs/DATASETS.md for a full troubleshooting guide.")
        sys.exit(result.returncode)

    # Optional: extract a sample subset
    if limit is not None:
        _extract_sample(dest, limit)
        return

    print(f"\nDownload complete. Files are in: {dest}")
    print("Reminder: never commit data/datasets/ to git.")


def _extract_sample(base_dir: Path, limit: int) -> None:
    """
    Copy at most `limit` image-like files from base_dir into base_dir/sample/.
    The full archive download already happened; this just selects a subset.
    """
    exts = {".jpg", ".jpeg", ".png", ".pdf"}
    sample_dir = base_dir / "sample"
    sample_dir.mkdir(exist_ok=True)

    all_files = sorted(
        f for f in base_dir.rglob("*")
        if f.is_file() and f.suffix.lower() in exts and "sample" not in f.parts
    )

    if not all_files:
        print(f"No image/PDF files found under {base_dir} to sample.")
        return

    copied = 0
    for src in all_files[:limit]:
        shutil.copy2(src, sample_dir / src.name)
        copied += 1

    print(f"\nSample created: {copied} file(s) copied to {sample_dir}")
    print(f"Full dataset remains at: {base_dir}")
    print("Reminder: never commit data/datasets/ to git.")


# ---------------------------------------------------------------------------
# FUNSD download
# ---------------------------------------------------------------------------

def download_funsd_sample(limit: int) -> None:
    """Download a small FUNSD sample via Hugging Face datasets library."""
    try:
        from datasets import load_dataset  # type: ignore[import]
    except ImportError:
        print(
            "ERROR: 'datasets' package not installed.\n"
            "Install it with: pip install datasets\n"
            "Then retry."
        )
        sys.exit(1)

    dest = _DATA_DIR / "funsd_sample"
    dest.mkdir(parents=True, exist_ok=True)
    print(f"Downloading up to {limit} FUNSD samples to {dest} ...")
    ds = load_dataset("nielsr/funsd", split="train", streaming=True)
    count = 0
    for i, sample in enumerate(ds):
        if i >= limit:
            break
        import json as _json
        (dest / f"sample_{i:04d}.json").write_text(
            _json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        count = i + 1
    print(f"Done. {count} samples written to {dest}")


# ---------------------------------------------------------------------------
# Default print_links
# ---------------------------------------------------------------------------

def print_links() -> None:
    print("\nActionRail Finance — Dataset Reference")
    print("=" * 60)
    print("No files will be downloaded unless you pass --download or --limit.")
    print(f"Local dataset directory: {_DATA_DIR}\n")
    for key, meta in DATASET_LINKS.items():
        print(f"  [{key}]  {meta['description']}")
        for field in ("kaggle", "huggingface", "zenodo", "github", "official"):
            if field in meta:
                print(f"    {field:12s}: {meta[field]}")
        print(f"    notes       : {meta['notes']}")
        print()
    print("Kaggle setup and download:")
    print("  python scripts/download_sample_datasets.py --check-kaggle")
    print("  python scripts/download_sample_datasets.py --source kaggle-invoices --instructions")
    print("  python scripts/download_sample_datasets.py --source kaggle-invoices --download")
    print()
    print("FUNSD sample (no login required):")
    print("  python scripts/download_sample_datasets.py --source funsd --limit 20")
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="ActionRail Finance — dataset download helper"
    )
    parser.add_argument(
        "--source",
        default=None,
        choices=list(DATASET_LINKS.keys()),
        metavar="SOURCE",
        help=f"Dataset source. Choices: {', '.join(DATASET_LINKS)}",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Actually download the dataset (requires credentials for Kaggle sources).",
    )
    parser.add_argument(
        "--instructions",
        action="store_true",
        help="Print the download command for the chosen source without downloading.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "For 'funsd': max samples to download. "
            "For 'kaggle-invoices': extract this many files into a sample/ sub-dir "
            "after the full download."
        ),
    )
    parser.add_argument(
        "--check-kaggle",
        action="store_true",
        help="Check Kaggle credentials and package availability.",
    )
    args = parser.parse_args()

    # Global check
    if args.check_kaggle:
        check_kaggle()
        return

    # No source: just print links
    if args.source is None:
        print_links()
        return

    # Instructions mode
    if args.instructions:
        if args.source == "kaggle-invoices":
            print_kaggle_instructions()
        else:
            meta = DATASET_LINKS[args.source]
            print(f"\n[{args.source}] {meta['description']}")
            for field in ("kaggle", "huggingface", "zenodo", "github", "official"):
                if field in meta:
                    print(f"  {field}: {meta[field]}")
            print(f"  notes: {meta['notes']}")
        return

    # Download mode
    if args.download:
        if args.source == "kaggle-invoices":
            download_kaggle_invoices(limit=args.limit)
        elif args.source == "funsd":
            download_funsd_sample(limit=args.limit or 20)
        else:
            meta = DATASET_LINKS[args.source]
            if not meta["auto_download"]:
                print(f"\n'{args.source}' cannot be auto-downloaded.")
                print(f"Description: {meta['description']}")
                print(f"Notes: {meta['notes']}")
                for field in ("kaggle", "huggingface", "zenodo", "github", "official"):
                    if field in meta:
                        print(f"  {field}: {meta[field]}")
                print("\nDownload manually and place files under data/datasets/.")
            else:
                print(f"No download path implemented for '{args.source}'.")
        return

    # Source given but neither --download nor --instructions: print source info
    if args.limit is not None and args.source == "funsd":
        # Legacy: --source funsd --limit N still works without explicit --download
        download_funsd_sample(args.limit)
        return

    meta = DATASET_LINKS[args.source]
    print(f"\n[{args.source}] {meta['description']}")
    for field in ("kaggle", "huggingface", "zenodo", "github", "official"):
        if field in meta:
            print(f"  {field}: {meta[field]}")
    print(f"  notes: {meta['notes']}")
    if args.source == "kaggle-invoices":
        print()
        print("  Add --instructions to see the download command.")
        print("  Add --download to run the download.")


if __name__ == "__main__":
    main()

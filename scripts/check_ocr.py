"""
ActionRail Finance — OCR environment check.

Prints the status of every dependency required for image OCR without crashing.

Usage:
    python scripts/check_ocr.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    print("\nActionRail Finance — OCR Environment Check")
    print("=" * 60)

    all_ok = True

    # ------------------------------------------------------------------ #
    # 1. Pillow
    # ------------------------------------------------------------------ #
    try:
        from PIL import Image  # noqa: F401
        import importlib.metadata
        try:
            pil_version = importlib.metadata.version("Pillow")
        except Exception:
            pil_version = "installed (version unknown)"
        print(f"  Pillow           : OK (version {pil_version})")
    except ImportError:
        print("  Pillow           : MISSING")
        print("    Fix: pip install pillow")
        all_ok = False

    # ------------------------------------------------------------------ #
    # 2. pytesseract Python package
    # ------------------------------------------------------------------ #
    try:
        import pytesseract  # noqa: F401
        import importlib.metadata
        try:
            pt_version = importlib.metadata.version("pytesseract")
        except Exception:
            pt_version = "installed (version unknown)"
        print(f"  pytesseract      : OK (version {pt_version})")
    except ImportError:
        print("  pytesseract      : MISSING")
        print("    Fix: pip install pytesseract")
        all_ok = False

    # ------------------------------------------------------------------ #
    # 3. Tesseract binary on PATH
    # ------------------------------------------------------------------ #
    tess_on_path = shutil.which("tesseract")
    if tess_on_path:
        print(f"  tesseract binary : OK (found at {tess_on_path})")
    else:
        print("  tesseract binary : NOT FOUND on PATH")
        all_ok = False

    # ------------------------------------------------------------------ #
    # 4. Tesseract version via subprocess
    # ------------------------------------------------------------------ #
    if tess_on_path:
        try:
            result = subprocess.run(
                ["tesseract", "--version"],
                capture_output=True, text=True, timeout=10,
            )
            version_line = (result.stdout or result.stderr or "").splitlines()[0]
            print(f"  tesseract version: {version_line.strip()}")
        except Exception as exc:
            print(f"  tesseract version: could not determine ({exc})")
    else:
        print("  tesseract version: skipped (binary not found)")

    # ------------------------------------------------------------------ #
    # 5. pytesseract → tesseract handshake
    # ------------------------------------------------------------------ #
    print()
    try:
        import pytesseract as pt
        ver = pt.get_tesseract_version()
        print(f"  pytesseract+tesseract handshake: OK (version {ver})")
    except ImportError:
        print("  pytesseract+tesseract handshake: SKIPPED (pytesseract not installed)")
    except Exception as exc:
        print(f"  pytesseract+tesseract handshake: FAILED ({type(exc).__name__})")
        print(f"    {exc}")
        all_ok = False

    # ------------------------------------------------------------------ #
    # 6. Verdict + fix instructions
    # ------------------------------------------------------------------ #
    print()
    if all_ok:
        print("  Status: READY — image OCR should work when uploading via the dashboard.")
    else:
        print("  Status: NOT READY — fix the issues above before image OCR will work.")
        print()
        print("  Install steps:")
        print("    pip install pytesseract pillow")
        print()
        print("  Tesseract binary (Windows):")
        print("    Download: https://github.com/UB-Mannheim/tesseract/wiki")
        print("    Then add to PATH for the current session:")
        print("      $env:Path += \";C:\\Program Files\\Tesseract-OCR\"")
        print()
        print("  Permanent PATH fix (Windows) — run as administrator:")
        print(
            "    [Environment]::SetEnvironmentVariable("
            "\"Path\","
            " $env:Path + \";C:\\Program Files\\Tesseract-OCR\","
            " [System.EnvironmentVariableTarget]::Machine"
            ")"
        )
        print()
        print("  Linux / macOS:")
        print("    sudo apt-get install tesseract-ocr    # Debian/Ubuntu")
        print("    brew install tesseract                # macOS")

    print()


if __name__ == "__main__":
    main()

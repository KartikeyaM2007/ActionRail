"""
Optional OCR module for ActionRail Finance.

Design rules:
- OCR is NEVER required. The app works without it.
- All OCR dependencies (pytesseract, Pillow, Tesseract binary) are optional.
- If anything is missing, return status="not_available" with helpful notes.
- Never crash on import or on function call.
- Never use paid/external OCR APIs.
- This module is the single OCR callsite in the codebase.

Usage in the upload route:
    from app.ocr import ocr_image_bytes
    result = ocr_image_bytes(file_bytes, filename="invoice.jpg")
    if result["status"] == "ok" and result["text"]:
        # use result["text"] with extract_fields_from_text()
"""
from __future__ import annotations

from typing import Any


def ocr_image_bytes(data: bytes, filename: str | None = None) -> dict[str, Any]:
    """
    Attempt OCR on raw image bytes using pytesseract + Pillow.

    Returns:
        {
            "status": "ok" | "not_available" | "failed",
            "engine": "pytesseract" | "none",
            "text": str | None,
            "notes": list[str],
        }

    - "ok"            — OCR succeeded; text is non-empty.
    - "not_available" — a required library or binary is missing; install instructions are in notes.
    - "failed"        — libraries are present but OCR raised an unexpected error.
    """
    notes: list[str] = []

    # ------------------------------------------------------------------ #
    # 1. Try importing Pillow (required to decode image bytes)
    # ------------------------------------------------------------------ #
    try:
        from PIL import Image  # type: ignore[import]
        import io
    except ImportError:
        notes.append(
            "Pillow is not installed. Run: pip install pillow"
        )
        notes.append(
            "Without Pillow, image OCR is unavailable. "
            "Enter invoice fields manually or install Pillow + pytesseract."
        )
        return {"status": "not_available", "engine": "none", "text": None, "notes": notes}

    # ------------------------------------------------------------------ #
    # 2. Try importing pytesseract
    # ------------------------------------------------------------------ #
    try:
        import pytesseract  # type: ignore[import]
    except ImportError:
        notes.append(
            "pytesseract is not installed. Run: pip install pytesseract"
        )
        notes.append(
            "Also install the Tesseract binary (see docs/OCR.md)."
        )
        return {"status": "not_available", "engine": "none", "text": None, "notes": notes}

    # ------------------------------------------------------------------ #
    # 3. Attempt OCR
    # ------------------------------------------------------------------ #
    try:
        img = Image.open(io.BytesIO(data))
        text = pytesseract.image_to_string(img)
        stripped = text.strip()
        if not stripped:
            notes.append("OCR ran but returned empty text. Image may be low-quality or blank.")
            return {"status": "not_available", "engine": "pytesseract", "text": None, "notes": notes}
        return {"status": "ok", "engine": "pytesseract", "text": stripped, "notes": notes}

    except Exception as exc:
        msg = str(exc)
        exc_type = type(exc).__name__

        # Tesseract binary not found (common on Windows when PATH is not set)
        if "TesseractNotFoundError" in exc_type or "tesseract is not installed" in msg.lower() or "which: no tesseract" in msg.lower():
            notes.append(
                "Tesseract binary not found. "
                "Install from https://github.com/UB-Mannheim/tesseract/wiki and add to PATH."
            )
            notes.append("See docs/OCR.md for platform-specific setup instructions.")
            return {"status": "not_available", "engine": "pytesseract", "text": None, "notes": notes}

        # Any other OCR error
        notes.append(f"OCR error ({exc_type}): {msg[:200]}")
        return {"status": "failed", "engine": "pytesseract", "text": None, "notes": notes}

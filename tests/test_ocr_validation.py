"""
Tests for Phase 2B-validation: OCR check/sample scripts, USD extraction improvements.

All tests run without real Tesseract or internet access.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

_REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Per-test DB + upload dir isolation
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    from app import main, store

    fresh = store.connect(tmp_path / "test.db")
    store.init_db(fresh)
    store.seed_demo(fresh)
    monkeypatch.setattr(main, "conn", fresh)

    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr(main, "_UPLOAD_DIR", upload_dir)
    yield
    fresh.close()


@pytest.fixture()
def client():
    return TestClient(app, follow_redirects=False)


def _load_script(name: str):
    path = _REPO_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# 1. check_ocr.py exits cleanly when dependencies are missing
# ---------------------------------------------------------------------------

def test_check_ocr_exits_cleanly_no_tesseract(monkeypatch, capsys):
    """check_ocr.py must not raise even when Tesseract binary is absent."""
    import shutil

    mod = _load_script("check_ocr")
    # Simulate tesseract not found in PATH
    monkeypatch.setattr(shutil, "which", lambda name: None if name == "tesseract" else shutil.which(name))
    mod.main()
    out = capsys.readouterr().out
    assert "tesseract binary" in out.lower() or "NOT FOUND" in out or "path" in out.lower()


def test_check_ocr_exits_cleanly_no_pytesseract(monkeypatch, capsys):
    """check_ocr.py handles missing pytesseract gracefully."""
    import builtins
    real_import = builtins.__import__

    def patched(name, *args, **kwargs):
        if name in ("pytesseract",):
            raise ImportError(f"No module named '{name}'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", patched)
    mod = _load_script("check_ocr")
    mod.main()
    out = capsys.readouterr().out
    assert "pytesseract" in out.lower()
    assert "MISSING" in out or "not installed" in out.lower()


# ---------------------------------------------------------------------------
# 2. run_ocr_sample.py exits cleanly when sample folder missing or empty
# ---------------------------------------------------------------------------

def test_run_ocr_sample_missing_folder(tmp_path, capsys):
    mod = _load_script("run_ocr_sample")
    mod.run_on_folder(tmp_path / "does_not_exist", limit=5, save_report=False)
    out = capsys.readouterr().out
    assert "does not exist" in out.lower() or "ERROR" in out


def test_run_ocr_sample_empty_folder(tmp_path, capsys):
    empty = tmp_path / "empty_sample"
    empty.mkdir()
    mod = _load_script("run_ocr_sample")
    mod.run_on_folder(empty, limit=5, save_report=False)
    out = capsys.readouterr().out
    assert "no image" in out.lower() or "found" in out.lower()


# ---------------------------------------------------------------------------
# 3. run_ocr_sample.py works with mocked OCR on fake image files
# ---------------------------------------------------------------------------

_MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
    b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
    b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_run_ocr_sample_with_mocked_ocr(tmp_path, monkeypatch, capsys):
    sample_dir = tmp_path / "sample"
    sample_dir.mkdir()
    (sample_dir / "test.jpg").write_bytes(_MINIMAL_PNG)

    # Monkeypatch ocr_image_bytes to return a fake ok result
    import app.ocr as ocr_mod
    monkeypatch.setattr(
        ocr_mod,
        "ocr_image_bytes",
        lambda data, **kwargs: {
            "status": "ok",
            "engine": "pytesseract",
            "text": "Invoice no: TEST-001 Total: $1,234.56",
            "notes": [],
        },
    )

    mod = _load_script("run_ocr_sample")
    mod.run_on_folder(sample_dir, limit=5, save_report=False)
    out = capsys.readouterr().out
    assert "ok" in out.lower()
    assert "TEST-001" in out or "1,234" in out


# ---------------------------------------------------------------------------
# 4–7. USD extraction improvements
# ---------------------------------------------------------------------------

from app.extraction import extract_fields_from_text


def test_usd_amount_bare():
    # $ on its own line (as it appears in real OCR text) should extract
    result = extract_fields_from_text("Invoice no: INV-001\nSeller: Acme Corp\nAmount: $1,234.56")
    assert result["fields"].get("amount") == 1234.56


def test_usd_amount_labelled():
    result = extract_fields_from_text("Amount Due: $1,234.56\nClient: Acme Corp")
    assert result["fields"].get("amount") == 1234.56


def test_invoice_number_hash():
    result = extract_fields_from_text("Invoice # 84652373\nDate: 01/01/2024")
    assert result["fields"].get("invoice_id") == "84652373"


def test_currency_usd_from_dollar_sign():
    result = extract_fields_from_text("Total $ 500.00")
    assert result["fields"].get("currency") == "USD"


# ---------------------------------------------------------------------------
# 8. Existing INR/GST extraction still works
# ---------------------------------------------------------------------------

def test_inr_amount_still_works():
    # INR prefix on its own context line should extract
    result = extract_fields_from_text("Invoice No: INV-2001\nVendor: Acme Services\nTotal: INR 83,000")
    assert result["fields"].get("amount") == 83000.0
    assert result["fields"].get("currency") == "INR"


def test_gst_still_extracted():
    result = extract_fields_from_text(
        "GST: 27ABCDE1234F1Z5\nAmount: INR 50,000"
    )
    assert result["fields"].get("gst_number") == "27ABCDE1234F1Z5"


# ---------------------------------------------------------------------------
# 9. Existing PDF upload still passes
# ---------------------------------------------------------------------------

_MINIMAL_PDF = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj
xref
0 4
0000000000 65535 f\r
0000000009 00000 n\r
0000000058 00000 n\r
0000000115 00000 n\r
trailer<</Size 4/Root 1 0 R>>
startxref
190
%%EOF"""


def test_pdf_upload_unaffected(client: TestClient):
    r = client.post(
        "/dashboard/invoices/upload",
        files={"file": ("inv.pdf", _MINIMAL_PDF, "application/pdf")},
        data={"invoice_id": "INV-TEST", "vendor": "Acme Services", "amount": "10000"},
    )
    assert r.status_code == 303


# ---------------------------------------------------------------------------
# 10. Image upload without OCR still passes
# ---------------------------------------------------------------------------

def test_image_upload_no_ocr_passes(client: TestClient, monkeypatch):
    import app.ocr as ocr_mod
    monkeypatch.setattr(
        ocr_mod,
        "ocr_image_bytes",
        lambda data, **kwargs: {
            "status": "not_available",
            "engine": "none",
            "text": None,
            "notes": ["pytesseract not installed"],
        },
    )
    r = client.post(
        "/dashboard/invoices/upload",
        files={"file": ("inv.png", _MINIMAL_PNG, "image/png")},
        data={"invoice_id": "INV-TEST", "vendor": "Acme Services", "amount": "10000"},
    )
    assert r.status_code == 303


# ---------------------------------------------------------------------------
# 11. Existing API JSON shapes
# ---------------------------------------------------------------------------

def test_api_shapes_unchanged(client: TestClient):
    r = client.get("/health")
    assert r.json() == {"status": "ok", "service": "actionrail-finance"}
    r = client.get("/actionrail/manifest.json")
    assert r.json()["name"] == "ActionRail Finance"

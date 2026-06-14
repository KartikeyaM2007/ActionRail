"""
Tests for Phase 2B: optional OCR module, dataset tools, and upload flow with OCR.

All tests run without real Kaggle files, without internet, and without
Tesseract installed. pytesseract / Pillow / Tesseract being absent is the
normal CI case and all tests must pass in that state.
"""
from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.dash_helpers import dash_get, dash_post

_REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Per-test DB isolation (same pattern as other test files)
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


# ---------------------------------------------------------------------------
# Minimal PNG bytes for upload tests
# ---------------------------------------------------------------------------

_MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
    b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
    b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)

# ---------------------------------------------------------------------------
# 1. ocr_image_bytes returns not_available gracefully with no pytesseract
# ---------------------------------------------------------------------------

def test_ocr_not_available_when_pytesseract_missing(monkeypatch):
    """With pytesseract absent, ocr_image_bytes returns status=not_available, no crash."""
    from app import ocr as ocr_mod

    # Simulate pytesseract not importable
    import builtins
    real_import = builtins.__import__

    def patched_import(name, *args, **kwargs):
        if name in ("pytesseract",):
            raise ImportError(f"No module named '{name}'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", patched_import)

    result = ocr_mod.ocr_image_bytes(_MINIMAL_PNG, filename="test.png")
    assert result["status"] == "not_available"
    assert result["engine"] == "none"
    assert result["text"] is None
    assert any("pytesseract" in note.lower() for note in result["notes"])


def test_ocr_not_available_when_pillow_missing(monkeypatch):
    """With Pillow absent, ocr_image_bytes returns status=not_available, no crash."""
    import builtins
    real_import = builtins.__import__

    def patched_import(name, *args, **kwargs):
        if name in ("PIL",):
            raise ImportError(f"No module named '{name}'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", patched_import)

    from app import ocr as ocr_mod
    result = ocr_mod.ocr_image_bytes(_MINIMAL_PNG, filename="test.png")
    # Either PIL or pytesseract missing → not_available
    assert result["status"] == "not_available"
    assert result["text"] is None


def test_ocr_returns_expected_keys():
    """ocr_image_bytes always returns the required response keys."""
    from app.ocr import ocr_image_bytes

    result = ocr_image_bytes(_MINIMAL_PNG, filename="test.png")
    assert set(result.keys()) >= {"status", "engine", "text", "notes"}
    assert result["status"] in ("ok", "not_available", "failed")
    assert isinstance(result["notes"], list)


# ---------------------------------------------------------------------------
# 2. Upload route still works for PNG/JPG without OCR
# ---------------------------------------------------------------------------

def test_upload_png_without_ocr_redirects(client: TestClient, monkeypatch):
    """Image upload redirects to review even when OCR is not available."""
    from app import ocr as ocr_mod

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

    # Step 1: upload → review (not transaction)
    r = dash_post(
        client,
        "/dashboard/invoices/upload",
        role="controller",
        files={"file": ("invoice.png", _MINIMAL_PNG, "image/png")},
    )
    assert r.status_code == 303
    assert "/dashboard/invoices/review/" in r.headers["location"]

    # Step 2: submit review with manual fields → transaction
    doc_id = r.headers["location"].split("/")[-1]
    r2 = dash_post(
        client,
        f"/dashboard/invoices/review/{doc_id}/submit",
        role="controller",
        data={"invoice_id": "INV-OCR-001", "vendor": "Acme Services", "amount": "30000"},
    )
    assert r2.status_code == 303
    assert "/dashboard/transactions/txn_" in r2.headers["location"]


# ---------------------------------------------------------------------------
# 3. Upload stores OCR notes when OCR is unavailable
# ---------------------------------------------------------------------------

def test_upload_stores_ocr_not_available_in_notes(client: TestClient, monkeypatch):
    """When OCR returns not_available, the note is stored in the uploaded_document."""
    from app import main as main_mod, ocr as ocr_mod
    from app.store import get_uploaded_document

    monkeypatch.setattr(
        ocr_mod,
        "ocr_image_bytes",
        lambda data, **kwargs: {
            "status": "not_available",
            "engine": "none",
            "text": None,
            "notes": ["pytesseract not installed. Run: pip install pytesseract"],
        },
    )

    # Step 1: upload → review
    r = dash_post(
        client,
        "/dashboard/invoices/upload",
        role="controller",
        files={"file": ("invoice.png", _MINIMAL_PNG, "image/png")},
    )
    assert r.status_code == 303
    doc_id = r.headers["location"].split("/")[-1]

    # Verify OCR notes stored before creating the transaction
    doc = get_uploaded_document(main_mod.conn, doc_id)
    assert doc is not None
    notes = doc["extraction_notes"]
    assert any("pytesseract" in n.lower() or "ocr" in n.lower() for n in notes)

    # Step 2: submit review → transaction (with manual fields)
    r2 = dash_post(
        client,
        f"/dashboard/invoices/review/{doc_id}/submit",
        role="controller",
        data={"invoice_id": "INV-OCR-002", "vendor": "Acme Services", "amount": "30000"},
    )
    assert r2.status_code == 303
    txn_id = r2.headers["location"].split("/")[-1]
    from app.policy import get_transaction
    txn = get_transaction(main_mod.conn, txn_id)
    evidence_urls = txn["invoice_json"].get("evidence_urls", [])
    assert any(f"local://uploaded_documents/{doc_id}" == url for url in evidence_urls)


# ---------------------------------------------------------------------------
# 4. Existing PDF upload tests still pass
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


def test_pdf_upload_still_works(client: TestClient):
    r = dash_post(
        client,
        "/dashboard/invoices/upload",
        role="controller",
        files={"file": ("invoice.pdf", _MINIMAL_PDF, "application/pdf")},
        data={
            "invoice_id": "INV-PDF-OCR-001",
            "vendor": "Acme Services",
            "amount": "50000",
        },
    )
    assert r.status_code == 303


# ---------------------------------------------------------------------------
# 5. Existing demo flows still pass
# ---------------------------------------------------------------------------

def test_existing_demo_flow_unaffected(client: TestClient):
    import re

    r = dash_post(client, "/dashboard/demo/approval_required", role="controller")
    assert r.status_code == 303
    txn_id = re.search(r"txn_[a-f0-9]+", r.headers["location"]).group()
    r = dash_get(client, f"/dashboard/transactions/{txn_id}")
    assert r.status_code == 200
    assert "approval required" in r.text.lower()


# ---------------------------------------------------------------------------
# 6. Dataset inspect script handles missing path gracefully
# ---------------------------------------------------------------------------

def _load_script(script_path: Path, monkeypatch=None):
    spec = importlib.util.spec_from_file_location(script_path.stem, script_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_inspect_script_missing_path(tmp_path, capsys):
    mod = _load_script(_REPO_ROOT / "scripts" / "inspect_invoice_dataset.py")
    mod.inspect(tmp_path / "does_not_exist")
    out = capsys.readouterr().out
    assert "does not exist" in out.lower() or "ERROR" in out
    assert "download" in out.lower() or "Download" in out


# ---------------------------------------------------------------------------
# 7. Sample preparation script handles missing source gracefully
# ---------------------------------------------------------------------------

def test_prepare_samples_missing_source(tmp_path, capsys):
    mod = _load_script(_REPO_ROOT / "scripts" / "prepare_invoice_samples.py")
    count = mod.prepare_samples(
        source=tmp_path / "does_not_exist",
        dest=tmp_path / "sample",
        limit=5,
    )
    assert count == 0
    out = capsys.readouterr().out
    assert "does not exist" in out.lower() or "ERROR" in out


# ---------------------------------------------------------------------------
# 8. Sample preparation copies fake image files from a temp source
# ---------------------------------------------------------------------------

def test_prepare_samples_copies_images(tmp_path, capsys):
    mod = _load_script(_REPO_ROOT / "scripts" / "prepare_invoice_samples.py")

    # Create fake source with a few fake jpg files
    source = tmp_path / "fake_dataset"
    source.mkdir()
    for i in range(5):
        (source / f"invoice_{i:03d}.jpg").write_bytes(b"fake-jpg-data")
    (source / "notes.txt").write_text("not an image")  # should be skipped

    dest = tmp_path / "sample_out"
    count = mod.prepare_samples(source=source, dest=dest, limit=3)
    assert count == 3
    assert len(list(dest.glob("*.jpg"))) == 3

    # Text file must not have been copied
    assert not (dest / "notes.txt").exists()


# ---------------------------------------------------------------------------
# 9. Existing API JSON shapes unchanged
# ---------------------------------------------------------------------------

def test_json_api_shapes_unchanged(client: TestClient):
    r = client.get("/health")
    assert r.json() == {"status": "ok", "service": "actionrail-finance"}

    r = client.get("/actionrail/manifest.json")
    assert r.json()["name"] == "ActionRail Finance"

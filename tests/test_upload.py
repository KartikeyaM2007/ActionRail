"""Tests for Phase 2A/2D: invoice upload → review → transaction flow."""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import connect, init_db, seed_demo
from tests.dash_helpers import dash_get, dash_post


# ---------------------------------------------------------------------------
# Shared per-test DB + upload dir isolation
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
# Minimal test file fixtures
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

_MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
    b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
    b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _upload_and_get_doc_id(client: TestClient, file_bytes=_MINIMAL_PNG,
                            filename="invoice.png", content_type="image/png") -> str:
    """Helper: POST file to upload route, return doc_id from review redirect."""
    r = dash_post(
        client,
        "/dashboard/invoices/upload",
        role="controller",
        files={"file": (filename, file_bytes, content_type)},
    )
    assert r.status_code == 303, r.text
    location = r.headers["location"]
    assert "/dashboard/invoices/review/" in location, location
    return location.split("/")[-1]


def _submit_review(client: TestClient, doc_id: str, **fields):
    """Helper: POST to review submit with given fields, return response."""
    return dash_post(
        client,
        f"/dashboard/invoices/review/{doc_id}/submit",
        role="controller",
        data=fields,
    )


# ---------------------------------------------------------------------------
# 1. Upload page loads
# ---------------------------------------------------------------------------

def test_upload_page_loads(client: TestClient):
    r = dash_get(client, "/dashboard/invoices/upload", role="controller")
    assert r.status_code == 200
    assert "Upload invoice" in r.text
    assert "No real money moves" in r.text
    assert 'enctype="multipart/form-data"' in r.text


# ---------------------------------------------------------------------------
# 2. Invalid extension rejected
# ---------------------------------------------------------------------------

def test_upload_invalid_extension_rejected(client: TestClient):
    r = dash_post(
        client,
        "/dashboard/invoices/upload",
        role="controller",
        files={"file": ("malware.exe", b"MZ...", "application/octet-stream")},
    )
    assert r.status_code == 400
    assert "Unsupported" in r.text


# ---------------------------------------------------------------------------
# 3. POST upload → redirects to review page (not transaction)
# ---------------------------------------------------------------------------

def test_upload_redirects_to_review_not_transaction(client: TestClient):
    r = dash_post(
        client,
        "/dashboard/invoices/upload",
        role="controller",
        files={"file": ("invoice.png", _MINIMAL_PNG, "image/png")},
    )
    assert r.status_code == 303
    location = r.headers["location"]
    # Must go to review, not transaction
    assert "/dashboard/invoices/review/" in location
    assert "/dashboard/transactions/" not in location


# ---------------------------------------------------------------------------
# 4. Review page loads and is pre-filled
# ---------------------------------------------------------------------------

def test_review_page_loads(client: TestClient):
    doc_id = _upload_and_get_doc_id(client)
    r = dash_get(client, f"/dashboard/invoices/review/{doc_id}", role="controller")
    assert r.status_code == 200
    assert "Review extracted invoice" in r.text
    assert doc_id in r.text


def test_review_page_shows_extraction_notes(client: TestClient, monkeypatch):
    """Review page shows extraction notes from OCR."""
    import app.ocr as ocr_mod
    monkeypatch.setattr(
        ocr_mod,
        "ocr_image_bytes",
        lambda data, **kwargs: {
            "status": "ok", "engine": "pytesseract",
            "text": "Invoice no: INV-99\nGrand Total: $500.00",
            "notes": [],
        },
    )
    doc_id = _upload_and_get_doc_id(client)
    r = dash_get(client, f"/dashboard/invoices/review/{doc_id}", role="controller")
    assert r.status_code == 200
    # Extraction notes or pre-filled field value should appear
    assert "INV-99" in r.text or "invoice_id" in r.text


# ---------------------------------------------------------------------------
# 5. Full two-step flow: upload → review submit → transaction
# ---------------------------------------------------------------------------

def test_full_upload_review_submit_creates_transaction(client: TestClient):
    doc_id = _upload_and_get_doc_id(client)
    r = _submit_review(
        client, doc_id,
        invoice_id="INV-UPLOAD-001",
        vendor="Acme Services",
        amount="30000",
        currency="INR",
    )
    assert r.status_code == 303
    assert "/dashboard/transactions/txn_" in r.headers["location"]


def test_review_submit_transaction_detail_accessible(client: TestClient):
    doc_id = _upload_and_get_doc_id(client)
    r = _submit_review(
        client, doc_id,
        invoice_id="INV-UPLOAD-002",
        vendor="Acme Services",
        amount="30000",
    )
    assert r.status_code == 303
    txn_id = r.headers["location"].split("/")[-1]
    detail = dash_get(client, f"/dashboard/transactions/{txn_id}")
    assert detail.status_code == 200
    assert "INV-UPLOAD-002" in detail.text
    assert "Acme Services" in detail.text


# ---------------------------------------------------------------------------
# 6. Manual amount override wins
# ---------------------------------------------------------------------------

def test_manual_amount_wins_in_review(client: TestClient, monkeypatch):
    """Manual amount supplied in review form is used, regardless of OCR extraction."""
    import app.ocr as ocr_mod
    monkeypatch.setattr(
        ocr_mod,
        "ocr_image_bytes",
        lambda data, **kwargs: {
            "status": "ok", "engine": "pytesseract",
            "text": "Invoice no: TEST-001\nItems qty 4,00\n3,00",  # no labelled total
            "notes": [],
        },
    )
    doc_id = _upload_and_get_doc_id(client)
    r = _submit_review(
        client, doc_id,
        invoice_id="TEST-001",
        vendor="Acme Services",
        amount="99999",
    )
    assert r.status_code == 303
    txn_id = r.headers["location"].split("/")[-1]
    from app import main as main_mod
    from app.policy import get_transaction
    txn = get_transaction(main_mod.conn, txn_id)
    assert float(txn["invoice_json"]["amount"]) == 99999.0


# ---------------------------------------------------------------------------
# 7. Missing amount on review submit returns 400
# ---------------------------------------------------------------------------

def test_review_submit_missing_amount_returns_400(client: TestClient, monkeypatch):
    import app.ocr as ocr_mod
    monkeypatch.setattr(
        ocr_mod,
        "ocr_image_bytes",
        lambda data, **kwargs: {
            "status": "not_available", "engine": "none", "text": None, "notes": [],
        },
    )
    doc_id = _upload_and_get_doc_id(client)
    r = _submit_review(
        client, doc_id,
        invoice_id="TEST-002",
        vendor="Acme Services",
        # no amount
    )
    assert r.status_code == 400
    assert "amount" in r.text.lower() or "Amount" in r.text


# ---------------------------------------------------------------------------
# 8. Evidence reference is attached to transaction
# ---------------------------------------------------------------------------

def test_evidence_ref_attached_to_transaction(client: TestClient):
    doc_id = _upload_and_get_doc_id(client, _MINIMAL_PDF, "invoice.pdf", "application/pdf")
    r = _submit_review(
        client, doc_id,
        invoice_id="INV-PDF-001",
        vendor="Acme Services",
        amount="50000",
    )
    assert r.status_code == 303
    txn_id = r.headers["location"].split("/")[-1]
    from app import main as main_mod
    from app.policy import get_transaction
    from app.store import get_uploaded_document
    txn = get_transaction(main_mod.conn, txn_id)
    evidence_urls = txn["invoice_json"].get("evidence_urls", [])
    assert any(f"local://uploaded_documents/{doc_id}" == url for url in evidence_urls)
    doc = get_uploaded_document(main_mod.conn, doc_id)
    assert doc is not None
    assert len(doc["sha256"]) == 64
    assert doc["original_filename"] == "invoice.pdf"


# ---------------------------------------------------------------------------
# 9. PDF extraction flow works end-to-end
# ---------------------------------------------------------------------------

def test_pdf_upload_flow(client: TestClient):
    doc_id = _upload_and_get_doc_id(client, _MINIMAL_PDF, "invoice.pdf", "application/pdf")
    r = _submit_review(
        client, doc_id,
        invoice_id="INV-PDF-002",
        vendor="Acme Services",
        amount="10000",
    )
    assert r.status_code == 303


# ---------------------------------------------------------------------------
# 10. OCR unavailable path still works with manual fields
# ---------------------------------------------------------------------------

def test_image_upload_no_ocr_flow(client: TestClient, monkeypatch):
    import app.ocr as ocr_mod
    monkeypatch.setattr(
        ocr_mod,
        "ocr_image_bytes",
        lambda data, **kwargs: {
            "status": "not_available", "engine": "none", "text": None,
            "notes": ["pytesseract not installed"],
        },
    )
    doc_id = _upload_and_get_doc_id(client)
    r = _submit_review(
        client, doc_id,
        invoice_id="INV-TEST",
        vendor="Acme Services",
        amount="10000",
    )
    assert r.status_code == 303


# ---------------------------------------------------------------------------
# 11. OCR available path: extracted fields prefill review form
# ---------------------------------------------------------------------------

def test_image_upload_with_mocked_ocr(client: TestClient, monkeypatch):
    import app.ocr as ocr_mod
    monkeypatch.setattr(
        ocr_mod,
        "ocr_image_bytes",
        lambda data, **kwargs: {
            "status": "ok", "engine": "pytesseract",
            "text": "Invoice no: INV-OCR-001\nGrand Total: $1,234.56",
            "notes": [],
        },
    )
    doc_id = _upload_and_get_doc_id(client)
    review = dash_get(client, f"/dashboard/invoices/review/{doc_id}", role="controller")
    assert review.status_code == 200
    # Extracted invoice_id should be pre-filled
    assert "INV-OCR-001" in review.text
    # Extracted amount $1,234.56 → 1234.56 should appear
    assert "1234.56" in review.text or "1,234" in review.text


# ---------------------------------------------------------------------------
# 12. Extraction helpers
# ---------------------------------------------------------------------------

def test_extraction_fields_from_text():
    from app.extraction import extract_fields_from_text

    sample = (
        "INVOICE\n"
        "Invoice No: INV-9900\n"
        "Date: 2026-06-13\n"
        "Due Date: 2026-06-25\n"
        "Total Amount: INR 1,50,000\n"
        "GST: 27ABCDE1234F1Z5\n"
    )
    result = extract_fields_from_text(sample)
    assert "fields" in result
    assert "notes" in result
    fields = result["fields"]
    assert fields.get("amount") == 150000.0
    assert fields.get("currency") == "INR"
    assert fields.get("gst_number") == "27ABCDE1234F1Z5"


def test_extraction_returns_empty_on_empty_text():
    from app.extraction import extract_fields_from_text
    result = extract_fields_from_text("")
    assert isinstance(result["fields"], dict)
    assert isinstance(result["notes"], list)


def test_pdf_extraction_on_minimal_pdf(tmp_path):
    from app.extraction import extract_text_from_pdf
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(_MINIMAL_PDF)
    text, status = extract_text_from_pdf(pdf_path)
    assert status in ("ok", "empty")


def test_pdf_extraction_on_non_pdf(tmp_path):
    from app.extraction import extract_text_from_pdf
    bad_path = tmp_path / "notapdf.pdf"
    bad_path.write_bytes(b"this is not a pdf at all")
    text, status = extract_text_from_pdf(bad_path)
    assert text is None
    assert "not_a_pdf" in status or "extraction_error" in status


# ---------------------------------------------------------------------------
# 13. Existing demo flows still work
# ---------------------------------------------------------------------------

def test_existing_demo_flows_unaffected(client: TestClient):
    r = dash_post(client, "/dashboard/demo/approval_required", role="controller")
    assert r.status_code == 303
    txn_id = re.search(r"/dashboard/transactions/(txn_[a-f0-9]+)", r.headers["location"]).group(1)
    detail = dash_get(client, f"/dashboard/transactions/{txn_id}")
    assert detail.status_code == 200
    assert "approval required" in detail.text.lower()


# ---------------------------------------------------------------------------
# 14. API JSON shapes unchanged
# ---------------------------------------------------------------------------

def test_json_api_shapes_unchanged(client: TestClient):
    r = client.get("/health")
    assert r.json() == {"status": "ok", "service": "actionrail-finance"}
    r = client.get("/actionrail/manifest.json")
    j = r.json()
    assert j["name"] == "ActionRail Finance"
    assert "preflight_action" in j["tools"]


# ---------------------------------------------------------------------------
# 15. Dashboard shows upload link
# ---------------------------------------------------------------------------

def test_dashboard_shows_upload_link(client: TestClient):
    r = dash_get(client, "/dashboard", role="controller")
    assert r.status_code == 200
    assert "Upload real invoice" in r.text
    assert "/dashboard/invoices/upload" in r.text

"""
Tests for Phase 2D: the two-step upload review flow.

All tests run without internet, real Kaggle files, or Tesseract.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.dash_helpers import dash_get, dash_post

_MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
    b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
    b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)

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


def _upload_file(client, file_bytes=_MINIMAL_PNG, filename="invoice.png", content_type="image/png"):
    r = dash_post(
        client,
        "/dashboard/invoices/upload",
        role="controller",
        files={"file": (filename, file_bytes, content_type)},
    )
    assert r.status_code == 303
    return r.headers["location"].split("/")[-1]


# ---------------------------------------------------------------------------
# 1. Upload page loads
# ---------------------------------------------------------------------------

def test_upload_page_loads(client):
    r = dash_get(client, "/dashboard/invoices/upload", role="controller")
    assert r.status_code == 200
    assert "Upload invoice" in r.text
    assert "review" in r.text.lower()


# ---------------------------------------------------------------------------
# 2. POST upload → review redirect (not transaction detail)
# ---------------------------------------------------------------------------

def test_post_upload_redirects_to_review(client):
    r = dash_post(
        client,
        "/dashboard/invoices/upload",
        role="controller",
        files={"file": ("invoice.png", _MINIMAL_PNG, "image/png")},
    )
    assert r.status_code == 303
    loc = r.headers["location"]
    assert "/dashboard/invoices/review/" in loc
    assert "/dashboard/transactions/" not in loc


def test_post_upload_pdf_redirects_to_review(client):
    r = dash_post(
        client,
        "/dashboard/invoices/upload",
        role="controller",
        files={"file": ("invoice.pdf", _MINIMAL_PDF, "application/pdf")},
    )
    assert r.status_code == 303
    assert "/dashboard/invoices/review/" in r.headers["location"]


# ---------------------------------------------------------------------------
# 3. Review page loads for uploaded document
# ---------------------------------------------------------------------------

def test_review_page_loads(client):
    doc_id = _upload_file(client)
    r = dash_get(client, f"/dashboard/invoices/review/{doc_id}", role="controller")
    assert r.status_code == 200
    assert "Review extracted invoice" in r.text
    assert doc_id in r.text


def test_review_page_404_for_unknown_doc(client):
    r = dash_get(client, "/dashboard/invoices/review/doc_doesnotexist", role="controller")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# 4. Review page pre-fills extracted fields
# ---------------------------------------------------------------------------

def test_review_page_prefills_extracted_fields(client, monkeypatch):
    import app.ocr as ocr_mod
    monkeypatch.setattr(
        ocr_mod,
        "ocr_image_bytes",
        lambda data, **kwargs: {
            "status": "ok",
            "engine": "pytesseract",
            "text": "Invoice no: INV-PREFILL-001\nSeller: Prefill Corp\nGrand Total: $500.00",
            "notes": [],
        },
    )
    doc_id = _upload_file(client)
    r = dash_get(client, f"/dashboard/invoices/review/{doc_id}", role="controller")
    assert r.status_code == 200
    # Pre-filled invoice_id should appear in the form
    assert "INV-PREFILL-001" in r.text


# ---------------------------------------------------------------------------
# 5. Review submit with confirmed fields creates transaction
# ---------------------------------------------------------------------------

def test_review_submit_creates_transaction(client):
    doc_id = _upload_file(client)
    r = dash_post(
        client,
        f"/dashboard/invoices/review/{doc_id}/submit",
        role="controller",
        data={
            "invoice_id": "INV-REVIEW-001",
            "vendor": "Acme Services",
            "amount": "83000",
            "currency": "INR",
        },
    )
    assert r.status_code == 303
    assert "/dashboard/transactions/txn_" in r.headers["location"]


def test_review_submit_missing_all_required_fields_returns_400(client):
    doc_id = _upload_file(client)
    r = dash_post(
        client,
        f"/dashboard/invoices/review/{doc_id}/submit",
        role="controller",
        data={},  # nothing
    )
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# 6. Manual amount override wins
# ---------------------------------------------------------------------------

def test_manual_amount_override_wins(client, monkeypatch):
    import app.ocr as ocr_mod
    monkeypatch.setattr(
        ocr_mod,
        "ocr_image_bytes",
        lambda data, **kwargs: {
            "status": "ok",
            "engine": "pytesseract",
            "text": "Invoice no: TEST-OVERRIDE\nItems qty 4,00",
            "notes": [],
        },
    )
    doc_id = _upload_file(client)
    r = dash_post(
        client,
        f"/dashboard/invoices/review/{doc_id}/submit",
        role="controller",
        data={
            "invoice_id": "TEST-OVERRIDE",
            "vendor": "Acme Services",
            "amount": "77777",  # manual
        },
    )
    assert r.status_code == 303
    txn_id = r.headers["location"].split("/")[-1]
    from app import main as m
    from app.policy import get_transaction
    txn = get_transaction(m.conn, txn_id)
    assert float(txn["invoice_json"]["amount"]) == 77777.0


# ---------------------------------------------------------------------------
# 7. Missing amount returns 400 with clear message
# ---------------------------------------------------------------------------

def test_review_submit_missing_amount_returns_400(client, monkeypatch):
    import app.ocr as ocr_mod
    monkeypatch.setattr(
        ocr_mod,
        "ocr_image_bytes",
        lambda data, **kwargs: {
            "status": "not_available", "engine": "none", "text": None, "notes": [],
        },
    )
    doc_id = _upload_file(client)
    r = dash_post(
        client,
        f"/dashboard/invoices/review/{doc_id}/submit",
        role="controller",
        data={"invoice_id": "X", "vendor": "Acme"},  # no amount
    )
    assert r.status_code == 400
    assert "amount" in r.text.lower() or "Amount" in r.text


# ---------------------------------------------------------------------------
# 8. Evidence reference is attached to transaction
# ---------------------------------------------------------------------------

def test_evidence_ref_in_transaction(client):
    doc_id = _upload_file(client)
    r = dash_post(
        client,
        f"/dashboard/invoices/review/{doc_id}/submit",
        role="controller",
        data={"invoice_id": "INV-EVID", "vendor": "Acme Services", "amount": "10000"},
    )
    assert r.status_code == 303
    txn_id = r.headers["location"].split("/")[-1]
    from app import main as m
    from app.policy import get_transaction
    txn = get_transaction(m.conn, txn_id)
    evidence_urls = txn["invoice_json"].get("evidence_urls", [])
    assert any(f"local://uploaded_documents/{doc_id}" == url for url in evidence_urls)


# ---------------------------------------------------------------------------
# 9. Existing demo flow still works (regression)
# ---------------------------------------------------------------------------

def test_existing_demo_flow_unaffected(client):
    import re
    r = dash_post(client, "/dashboard/demo/approval_required", role="controller")
    assert r.status_code == 303
    txn_id = re.search(r"txn_[a-f0-9]+", r.headers["location"]).group()
    detail = dash_get(client, f"/dashboard/transactions/{txn_id}")
    assert detail.status_code == 200
    assert "approval required" in detail.text.lower()


# ---------------------------------------------------------------------------
# 10. API JSON shapes unchanged
# ---------------------------------------------------------------------------

def test_json_api_shapes_unchanged(client):
    r = client.get("/health")
    assert r.json() == {"status": "ok", "service": "actionrail-finance"}
    r = client.get("/actionrail/manifest.json")
    assert "preflight_action" in r.json()["tools"]

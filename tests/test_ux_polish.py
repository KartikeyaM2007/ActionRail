"""
Tests for Phase 2E: real-upload UX polish.

Verifies that key copy, warnings, and UX elements are present in the templates.
No real OCR, no real Kaggle files, no internet required.
"""
from __future__ import annotations

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


def _upload(client, monkeypatch=None, ocr_text=None):
    """Upload a PNG (with optional mocked OCR) and return the doc_id."""
    if monkeypatch and ocr_text:
        import app.ocr as ocr_mod
        monkeypatch.setattr(
            ocr_mod, "ocr_image_bytes",
            lambda data, **kwargs: {
                "status": "ok", "engine": "pytesseract",
                "text": ocr_text, "notes": [],
            },
        )
    elif monkeypatch:
        import app.ocr as ocr_mod
        monkeypatch.setattr(
            ocr_mod, "ocr_image_bytes",
            lambda data, **kwargs: {
                "status": "not_available", "engine": "none", "text": None, "notes": [],
            },
        )
    r = dash_post(
        client,
        "/dashboard/invoices/upload",
        role="controller",
        files={"file": ("invoice.png", _MINIMAL_PNG, "image/png")},
    )
    assert r.status_code == 303
    return r.headers["location"].split("/")[-1]


# ---------------------------------------------------------------------------
# 1. Upload page: review-before-transaction copy
# ---------------------------------------------------------------------------

def test_upload_page_contains_review_copy(client):
    r = dash_get(client, "/dashboard/invoices/upload", role="controller")
    assert r.status_code == 200
    body = r.text
    assert "review" in body.lower()
    assert "No real money moves" in body
    assert "confirm" in body.lower() or "before creating a transaction" in body.lower()


# ---------------------------------------------------------------------------
# 2. Review page: confirmation / safety copy
# ---------------------------------------------------------------------------

def test_review_page_contains_safety_copy(client, monkeypatch):
    doc_id = _upload(client, monkeypatch)
    r = dash_get(client, f"/dashboard/invoices/review/{doc_id}", role="controller")
    assert r.status_code == 200
    body = r.text
    assert "No real money moves" in body
    assert "simulated" in body.lower()
    assert "confirm" in body.lower() or "review" in body.lower()


# ---------------------------------------------------------------------------
# 3. Review page: manual review warning when amount missing
# ---------------------------------------------------------------------------

def test_review_page_shows_manual_review_warning_when_amount_missing(client, monkeypatch):
    # OCR returns no labeled total → amount won't be extracted
    doc_id = _upload(
        client, monkeypatch,
        ocr_text="Invoice no: INV-001\nItems qty 4,00"
    )
    r = dash_get(client, f"/dashboard/invoices/review/{doc_id}", role="controller")
    assert r.status_code == 200
    body = r.text
    assert "manual review required" in body.lower() or "not confidently extracted" in body.lower()
    assert "amount" in body.lower()


# ---------------------------------------------------------------------------
# 4. Review page: editable fields present and pre-filled from OCR
# ---------------------------------------------------------------------------

def test_review_page_has_editable_fields(client, monkeypatch):
    doc_id = _upload(
        client, monkeypatch,
        ocr_text="Invoice no: INV-PREFILL\nGrand Total: $500.00"
    )
    r = dash_get(client, f"/dashboard/invoices/review/{doc_id}", role="controller")
    assert r.status_code == 200
    body = r.text
    # Editable input fields must be present
    assert 'name="invoice_id"' in body
    assert 'name="vendor"' in body
    assert 'name="amount"' in body
    assert 'name="currency"' in body
    # Pre-filled value from OCR
    assert "INV-PREFILL" in body


# ---------------------------------------------------------------------------
# 5. Review page: extracted text in a collapsible details block
# ---------------------------------------------------------------------------

def test_review_page_has_extracted_text_collapsible(client, monkeypatch):
    doc_id = _upload(
        client, monkeypatch,
        ocr_text="Invoice no: INV-DETAILS\nDate: 2026-01-01\nGrand Total: $100.00"
    )
    r = dash_get(client, f"/dashboard/invoices/review/{doc_id}", role="controller")
    assert r.status_code == 200
    body = r.text
    assert "<details" in body
    assert "extracted text" in body.lower() or "Show extracted text" in body


# ---------------------------------------------------------------------------
# 6. Transaction detail: uploaded evidence section and reviewed stamp
# ---------------------------------------------------------------------------

def test_transaction_detail_shows_uploaded_evidence(client, monkeypatch):
    doc_id = _upload(client, monkeypatch)
    r = dash_post(
        client,
        f"/dashboard/invoices/review/{doc_id}/submit",
        role="controller",
        data={"invoice_id": "INV-EV-001", "vendor": "Acme Services", "amount": "50000"},
    )
    assert r.status_code == 303
    txn_id = r.headers["location"].split("/")[-1]
    detail = dash_get(client, f"/dashboard/transactions/{txn_id}")
    assert detail.status_code == 200
    body = detail.text
    # Uploaded evidence section
    assert "Uploaded evidence" in body
    assert doc_id in body
    assert "invoice.png" in body
    # SHA-256 short display
    assert "…" in body  # truncated SHA-256
    # Evidence reference
    assert f"local://uploaded_documents/{doc_id}" in body
    # Reviewed stamp
    assert "reviewed before transaction" in body.lower() or "confirmed by user" in body.lower()


# ---------------------------------------------------------------------------
# 7. Existing two-step upload flow still works
# ---------------------------------------------------------------------------

def test_two_step_upload_flow_still_works(client, monkeypatch):
    doc_id = _upload(client, monkeypatch)
    r = dash_post(
        client,
        f"/dashboard/invoices/review/{doc_id}/submit",
        role="controller",
        data={"invoice_id": "INV-FLOW-001", "vendor": "Acme Services", "amount": "30000"},
    )
    assert r.status_code == 303
    assert "/dashboard/transactions/txn_" in r.headers["location"]


# ---------------------------------------------------------------------------
# 8. Existing dashboard demo flow still works
# ---------------------------------------------------------------------------

def test_demo_flow_still_works(client):
    import re
    r = dash_post(client, "/dashboard/demo/approval_required", role="controller")
    assert r.status_code == 303
    txn_id = re.search(r"txn_[a-f0-9]+", r.headers["location"]).group()
    r = dash_get(client, f"/dashboard/transactions/{txn_id}")
    assert r.status_code == 200
    assert "approval required" in r.text.lower()


# ---------------------------------------------------------------------------
# 9. API JSON shapes unchanged
# ---------------------------------------------------------------------------

def test_api_shapes_unchanged(client):
    r = client.get("/health")
    assert r.json() == {"status": "ok", "service": "actionrail-finance"}
    r = client.get("/actionrail/manifest.json")
    assert "preflight_action" in r.json()["tools"]

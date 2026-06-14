"""
Tests for Phase 2C: safer extraction — currency, amount confidence gating.

None of these tests require internet, real Kaggle files, or Tesseract.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.extraction import _detect_currency, _extract_amount_with_confidence, extract_fields_from_text
from app.main import app
from tests.dash_helpers import dash_get, dash_post

_REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Per-test DB isolation
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
# Currency detection — must NOT infer from address/state abbreviations
# ---------------------------------------------------------------------------

def test_no_currency_from_indiana_address():
    # "IN 57228" is Indiana state abbreviation — must not produce INR
    assert _detect_currency("Lake Daniellefurt, IN 57228") is None


def test_no_currency_from_us_state_abbreviation():
    assert _detect_currency("North Douglas, AZ 95355") is None


def test_no_currency_from_us_state_in_sentence():
    # "IN" inside a normal address line must not produce INR
    result = extract_fields_from_text("Seller: Andrews, Kirby\n58861 Gonzalez Prairie IN 57228")
    assert result["fields"].get("currency") is None


def test_currency_usd_from_dollar():
    assert _detect_currency("Invoice total: $1,234.56") == "USD"


def test_currency_inr_from_inr_code():
    assert _detect_currency("Amount Due: INR 83,000") == "INR"


def test_currency_inr_from_rs():
    assert _detect_currency("Amount Due: Rs. 83,000") == "INR"


def test_currency_inr_from_rupee_symbol():
    assert _detect_currency("₹ 83,000") == "INR"


# ---------------------------------------------------------------------------
# Amount extraction — confidence gating
# ---------------------------------------------------------------------------

def test_no_amount_from_quantity():
    amount, notes = _extract_amount_with_confidence("No. Description Qty\n1. Product A 4,00\n2. Product B 3,00")
    assert amount is None
    assert any("manual review" in n.lower() or "not confidently" in n.lower() for n in notes)


def test_no_amount_from_tax_id():
    amount, notes = _extract_amount_with_confidence("Tax Id: 945-82-2137\nIBAN: GB75MCRL06841367619257")
    assert amount is None


def test_amount_from_amount_due_usd():
    amount, notes = _extract_amount_with_confidence("Invoice #001\nAmount Due: $1,234.56")
    assert amount == 1234.56
    assert any("1234.56" in n or "1,234" in n for n in notes)


def test_amount_from_grand_total_usd():
    amount, notes = _extract_amount_with_confidence("Grand Total: USD 1,234.56")
    assert amount == 1234.56


def test_amount_from_grand_total_inr():
    amount, notes = _extract_amount_with_confidence("Grand Total: INR 83,000")
    assert amount == 83000.0


def test_amount_from_inr_rupee_symbol():
    amount, notes = _extract_amount_with_confidence("Amount Due: ₹83,000")
    assert amount == 83000.0


def test_amount_rejects_implausibly_small_value():
    # Value < 10 should be rejected even on a labelled line
    amount, notes = _extract_amount_with_confidence("Amount Due: $5.00")
    assert amount is None


def test_amount_note_says_manual_review_when_missing():
    amount, notes = _extract_amount_with_confidence("Invoice no: 12345\nDate: 01/01/2024\nItems:\n1. Widget 2.00")
    assert amount is None
    assert any("manual review required" in n.lower() for n in notes)


# ---------------------------------------------------------------------------
# Full extract_fields_from_text tests
# ---------------------------------------------------------------------------

def test_no_false_positive_inr_from_us_address_full():
    text = (
        "Invoice no: 51109338\n"
        "Date of issue: 04/13/2013\n"
        "Seller: Andrews, Kirby and Valdez Becker Ltd\n"
        "58861 Gonzalez Prairie\n"
        "Lake Daniellefurt, IN 57228\n"
        "North Douglas, AZ 95355\n"
        "Tax Id: 945-82-2137\n"
    )
    result = extract_fields_from_text(text)
    # Currency should NOT be INR or USD — no explicit symbol or code
    assert result["fields"].get("currency") is None


def test_amount_and_currency_from_labelled_inr_text():
    text = "Invoice no: INV-2001\nVendor: Acme Services\nGrand Total: INR 83,000"
    result = extract_fields_from_text(text)
    assert result["fields"].get("amount") == 83000.0
    assert result["fields"].get("currency") == "INR"


# ---------------------------------------------------------------------------
# Upload route: manual amount override wins over OCR
# ---------------------------------------------------------------------------

_MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
    b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
    b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_manual_amount_override_wins(client: TestClient, monkeypatch):
    """Manual amount in review form overrides OCR extraction (two-step flow)."""
    import app.ocr as ocr_mod
    monkeypatch.setattr(
        ocr_mod,
        "ocr_image_bytes",
        lambda data, **kwargs: {
            "status": "ok",
            "engine": "pytesseract",
            "text": "Invoice no: TEST-001\nSome items 2,00\n3,00",
            "notes": [],
        },
    )
    # Step 1: upload → review
    r = dash_post(
        client,
        "/dashboard/invoices/upload",
        role="controller",
        files={"file": ("inv.png", _MINIMAL_PNG, "image/png")},
    )
    assert r.status_code == 303
    doc_id = r.headers["location"].split("/")[-1]
    # Step 2: submit review with manual amount
    r = dash_post(
        client,
        f"/dashboard/invoices/review/{doc_id}/submit",
        role="controller",
        data={"invoice_id": "TEST-001", "vendor": "Acme Services", "amount": "99999"},
    )
    assert r.status_code == 303
    txn_id = r.headers["location"].split("/")[-1]
    from app import main as main_mod
    from app.policy import get_transaction
    txn = get_transaction(main_mod.conn, txn_id)
    assert float(txn["invoice_json"]["amount"]) == 99999.0


def test_upload_without_confident_amount_returns_400(client: TestClient, monkeypatch):
    """Without manual amount on review submit, returns 400 (two-step flow)."""
    import app.ocr as ocr_mod
    monkeypatch.setattr(
        ocr_mod,
        "ocr_image_bytes",
        lambda data, **kwargs: {
            "status": "ok",
            "engine": "pytesseract",
            "text": "Invoice no: TEST-002\nItems: some stuff 2,00",  # no labelled total
            "notes": [],
        },
    )
    r = dash_post(
        client,
        "/dashboard/invoices/upload",
        role="controller",
        files={"file": ("inv.png", _MINIMAL_PNG, "image/png")},
    )
    assert r.status_code == 303
    doc_id = r.headers["location"].split("/")[-1]
    # Submit review without amount — should fail
    r = dash_post(
        client,
        f"/dashboard/invoices/review/{doc_id}/submit",
        role="controller",
        data={"invoice_id": "TEST-002", "vendor": "Acme Services"},
    )
    assert r.status_code == 400
    assert "amount" in r.text.lower() or "Amount" in r.text


def test_upload_400_message_mentions_manual_entry(client: TestClient, monkeypatch):
    """The 400 error on review submit mentions entering amount."""
    import app.ocr as ocr_mod
    monkeypatch.setattr(
        ocr_mod,
        "ocr_image_bytes",
        lambda data, **kwargs: {
            "status": "not_available", "engine": "none", "text": None, "notes": [],
        },
    )
    r = dash_post(
        client,
        "/dashboard/invoices/upload",
        role="controller",
        files={"file": ("inv.png", _MINIMAL_PNG, "image/png")},
    )
    assert r.status_code == 303
    doc_id = r.headers["location"].split("/")[-1]
    r = dash_post(
        client,
        f"/dashboard/invoices/review/{doc_id}/submit",
        role="controller",
        data={"vendor": "Acme", "invoice_id": "X"},
    )
    assert r.status_code == 400
    assert any(w in r.text.lower() for w in ("manually", "manual", "amount", "required"))


# ---------------------------------------------------------------------------
# Regression: existing extractions still work
# ---------------------------------------------------------------------------

def test_inr_amount_from_demo_text():
    text = "Invoice No: INV-2001 INR 83,000"
    result = extract_fields_from_text(text)
    # INR prefix on number — amount only extracted if on labelled line; not standalone here
    # Currency check: INR code present → should detect
    assert result["fields"].get("currency") == "INR"


def test_gst_still_extracted():
    result = extract_fields_from_text("GST: 27ABCDE1234F1Z5\nAmount Due: INR 50,000")
    assert result["fields"].get("gst_number") == "27ABCDE1234F1Z5"
    assert result["fields"].get("amount") == 50000.0


def test_pdf_upload_unaffected(client: TestClient):
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
    r = dash_post(
        client,
        "/dashboard/invoices/upload",
        role="controller",
        files={"file": ("inv.pdf", _MINIMAL_PDF, "application/pdf")},
        data={"invoice_id": "INV-PDF", "vendor": "Acme Services", "amount": "10000"},
    )
    assert r.status_code == 303


def test_api_shapes_unchanged(client: TestClient):
    r = client.get("/health")
    assert r.json() == {"status": "ok", "service": "actionrail-finance"}

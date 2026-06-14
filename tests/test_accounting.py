"""
Tests for Phase 3A: accounting sandbox writeback.

None of these tests require internet, real accounting providers,
real uploaded invoice files, OCR, or Tesseract.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

_MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
    b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
    b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)

# ---------------------------------------------------------------------------
# Per-test DB + upload dir + sandbox dir isolation
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

    # Point the accounting adapter at temp dirs so tests never write to data/
    from app import accounting
    draft_dir = tmp_path / "draft_bills"
    audit_dir = tmp_path / "audit_packets"
    draft_dir.mkdir()
    audit_dir.mkdir()
    monkeypatch.setattr(accounting, "_DRAFT_BILLS_DIR", draft_dir)
    monkeypatch.setattr(accounting, "_AUDIT_PACKETS_DIR", audit_dir)

    yield
    fresh.close()


@pytest.fixture()
def client():
    return TestClient(app, follow_redirects=False)


# ---------------------------------------------------------------------------
# Helper: run a full approval-required demo flow
# ---------------------------------------------------------------------------

def _full_executed_txn(client: TestClient) -> str:
    """Create an executed transaction via the demo flow. Returns txn_id."""
    r = client.post("/dashboard/demo/approval_required")
    assert r.status_code == 303
    txn_id = re.search(r"txn_[a-f0-9]+", r.headers["location"]).group()
    r = client.post(f"/dashboard/transactions/{txn_id}/approve")
    assert r.status_code == 303
    r = client.post(f"/dashboard/transactions/{txn_id}/execute")
    assert r.status_code == 303
    return txn_id


# ---------------------------------------------------------------------------
# 1. Adapter rejects non-executed transaction
# ---------------------------------------------------------------------------

def test_adapter_rejects_non_executed(tmp_path):
    from app.accounting import LocalAccountingSandboxAdapter
    adapter = LocalAccountingSandboxAdapter(
        draft_bills_dir=tmp_path / "db",
        audit_packets_dir=tmp_path / "ap",
    )
    txn = {"id": "txn_test", "status": "preflighted", "receipt_json": None}
    with pytest.raises(ValueError, match="writeback requires status='executed'"):
        adapter.create_draft_bill(txn)


# ---------------------------------------------------------------------------
# 2. Adapter creates draft bill JSON for executed transaction
# ---------------------------------------------------------------------------

def test_adapter_creates_draft_bill(tmp_path):
    from app.accounting import LocalAccountingSandboxAdapter

    draft_dir = tmp_path / "db"
    audit_dir = tmp_path / "ap"
    adapter = LocalAccountingSandboxAdapter(
        draft_bills_dir=draft_dir, audit_packets_dir=audit_dir
    )

    receipt = {
        "receipt_id": "rcpt_test001",
        "transaction_id": "txn_test001",
        "receipt_signature": "abc123",
        "payload": {},
    }
    txn = {
        "id": "txn_test001",
        "status": "executed",
        "receipt_json": json.dumps(receipt),
        "invoice_json": {
            "invoice_id": "INV-001",
            "vendor": "Acme Services",
            "amount": 83000.0,
            "currency": "INR",
            "evidence_urls": ["local://uploaded_documents/doc_test"],
        },
        "checks_json": [],
        "approval_json": {"approver_id": "controller_001"},
        "execution_json": {"status": "executed"},
    }

    result = adapter.create_draft_bill(txn)
    assert result.status == "draft_created"
    assert result.provider == "local_accounting_sandbox"
    assert result.external_id == "draft_txn_test001"

    # File must exist
    assert (draft_dir / "txn_test001.json").exists()
    bill_data = json.loads((draft_dir / "txn_test001.json").read_text())
    assert bill_data["vendor"] == "Acme Services"
    assert bill_data["amount"] == 83000.0
    assert bill_data["receipt_signature"] == "abc123"


# ---------------------------------------------------------------------------
# 3. Adapter creates audit packet JSON
# ---------------------------------------------------------------------------

def test_adapter_creates_audit_packet(tmp_path):
    from app.accounting import LocalAccountingSandboxAdapter

    draft_dir = tmp_path / "db"
    audit_dir = tmp_path / "ap"
    adapter = LocalAccountingSandboxAdapter(
        draft_bills_dir=draft_dir, audit_packets_dir=audit_dir
    )

    receipt = {"receipt_id": "rcpt_002", "receipt_signature": "sig002", "payload": {}}
    txn = {
        "id": "txn_002",
        "status": "executed",
        "receipt_json": json.dumps(receipt),
        "invoice_json": {"invoice_id": "INV-002", "vendor": "AWS", "amount": 12000.0, "currency": "USD"},
        "checks_json": [{"name": "vendor_verified", "status": "passed"}],
        "approval_json": None,
        "execution_json": None,
    }

    adapter.create_draft_bill(txn)
    assert (audit_dir / "txn_002.json").exists()
    audit_data = json.loads((audit_dir / "txn_002.json").read_text())
    assert audit_data["transaction_id"] == "txn_002"
    assert len(audit_data["checks_json"]) == 1
    assert audit_data["receipt_json"]["receipt_signature"] == "sig002"


# ---------------------------------------------------------------------------
# 4. Writeback result includes receipt signature
# ---------------------------------------------------------------------------

def test_writeback_result_includes_receipt_signature(tmp_path):
    from app.accounting import LocalAccountingSandboxAdapter

    adapter = LocalAccountingSandboxAdapter(
        draft_bills_dir=tmp_path / "db", audit_packets_dir=tmp_path / "ap"
    )
    receipt = {"receipt_id": "rcpt_003", "receipt_signature": "HMAC_SIG_003", "payload": {}}
    txn = {
        "id": "txn_003",
        "status": "executed",
        "receipt_json": receipt,  # also test dict receipt (not string)
        "invoice_json": {"invoice_id": "INV-003", "vendor": "Test"},
        "checks_json": [],
        "approval_json": None,
        "execution_json": None,
    }
    adapter.create_draft_bill(txn)
    bill = json.loads((tmp_path / "db" / "txn_003.json").read_text())
    assert bill["receipt_signature"] == "HMAC_SIG_003"


# ---------------------------------------------------------------------------
# 5. Writeback is idempotent in the DB
# ---------------------------------------------------------------------------

def test_writeback_idempotent(tmp_path):
    from app import main as main_mod
    from app.store import save_accounting_writeback, get_accounting_writeback

    conn = main_mod.conn
    save_accounting_writeback(
        conn,
        writeback_id="wb_idem1",
        transaction_id="txn_idem",
        provider="local_accounting_sandbox",
        status="draft_created",
        external_id="draft_txn_idem",
        result={"key": "value1"},
    )
    # Second call with same (transaction_id, provider) should update, not error
    save_accounting_writeback(
        conn,
        writeback_id="wb_idem2",
        transaction_id="txn_idem",
        provider="local_accounting_sandbox",
        status="draft_created",
        external_id="draft_txn_idem",
        result={"key": "value2"},
    )
    result = get_accounting_writeback(conn, "txn_idem", "local_accounting_sandbox")
    assert result is not None
    # Should have the updated result
    assert result["result"]["key"] == "value2"


# ---------------------------------------------------------------------------
# 6. DB table stores and retrieves writeback
# ---------------------------------------------------------------------------

def test_db_stores_and_retrieves_writeback():
    from app import main as main_mod
    from app.store import save_accounting_writeback, get_accounting_writeback

    conn = main_mod.conn
    save_accounting_writeback(
        conn,
        writeback_id="wb_store1",
        transaction_id="txn_store1",
        provider="local_accounting_sandbox",
        status="draft_created",
        external_id="draft_txn_store1",
        result={"provider": "local_accounting_sandbox", "status": "draft_created"},
    )
    row = get_accounting_writeback(conn, "txn_store1", "local_accounting_sandbox")
    assert row is not None
    assert row["transaction_id"] == "txn_store1"
    assert row["provider"] == "local_accounting_sandbox"
    assert row["result"]["status"] == "draft_created"


# ---------------------------------------------------------------------------
# 7. Dashboard does NOT show writeback button before execution
# ---------------------------------------------------------------------------

def test_no_writeback_button_before_execution(client: TestClient):
    r = client.post("/dashboard/demo/approval_required")
    assert r.status_code == 303
    txn_id = re.search(r"txn_[a-f0-9]+", r.headers["location"]).group()
    detail = client.get(f"/dashboard/transactions/{txn_id}")
    body = detail.text
    assert detail.status_code == 200
    assert "Create Accounting Sandbox Draft Bill" not in body
    assert "View Accounting Sandbox Writeback" not in body
    assert f'/writeback/accounting-sandbox' not in body


# ---------------------------------------------------------------------------
# 8. Dashboard shows create writeback button after execution (no writeback yet)
# ---------------------------------------------------------------------------

def test_writeback_create_button_shown_after_execution(client: TestClient):
    txn_id = _full_executed_txn(client)
    detail = client.get(f"/dashboard/transactions/{txn_id}")
    assert detail.status_code == 200
    body = detail.text
    assert "Create Accounting Sandbox Draft Bill" in body
    assert "View Accounting Sandbox Writeback" not in body


# ---------------------------------------------------------------------------
# 9. POST writeback creates result and redirects
# ---------------------------------------------------------------------------

def test_post_writeback_creates_and_redirects(client: TestClient):
    txn_id = _full_executed_txn(client)
    r = client.post(f"/dashboard/transactions/{txn_id}/writeback/accounting-sandbox")
    assert r.status_code == 303
    assert f"/dashboard/transactions/{txn_id}/writeback/accounting-sandbox" in r.headers["location"]


# ---------------------------------------------------------------------------
# 10. Re-clicking writeback POST is idempotent (redirects, no duplicate error)
# ---------------------------------------------------------------------------

def test_writeback_post_idempotent(client: TestClient):
    txn_id = _full_executed_txn(client)
    r1 = client.post(f"/dashboard/transactions/{txn_id}/writeback/accounting-sandbox")
    assert r1.status_code == 303
    r2 = client.post(f"/dashboard/transactions/{txn_id}/writeback/accounting-sandbox")
    assert r2.status_code == 303
    assert r2.headers["location"] == r1.headers["location"]


# ---------------------------------------------------------------------------
# 11. After writeback, detail page shows View (not Create)
# ---------------------------------------------------------------------------

def test_writeback_view_button_after_create(client: TestClient):
    txn_id = _full_executed_txn(client)
    client.post(f"/dashboard/transactions/{txn_id}/writeback/accounting-sandbox")
    detail = client.get(f"/dashboard/transactions/{txn_id}")
    body = detail.text
    assert "View Accounting Sandbox Writeback" in body
    assert "Create Accounting Sandbox Draft Bill" not in body


# ---------------------------------------------------------------------------
# 12. GET writeback page shows safety note
# ---------------------------------------------------------------------------

def test_writeback_page_shows_safety_note(client: TestClient):
    txn_id = _full_executed_txn(client)
    client.post(f"/dashboard/transactions/{txn_id}/writeback/accounting-sandbox")
    r = client.get(f"/dashboard/transactions/{txn_id}/writeback/accounting-sandbox")
    assert r.status_code == 200
    body = r.text.lower()
    assert "local accounting sandbox only" in body
    assert "no erp, bank, or ledger mutation performed" in body
    assert "integration-readiness" in body
    assert "draft_created" in body or "draft bill" in body


# ---------------------------------------------------------------------------
# 13. Writeback page does not expose absolute local paths
# ---------------------------------------------------------------------------

def test_writeback_page_no_absolute_paths(client: TestClient):
    txn_id = _full_executed_txn(client)
    client.post(f"/dashboard/transactions/{txn_id}/writeback/accounting-sandbox")
    r = client.get(f"/dashboard/transactions/{txn_id}/writeback/accounting-sandbox")
    body = r.text
    # Windows drive letters and common absolute path patterns
    assert not re.search(r"[A-Za-z]:\\", body)
    assert "data/accounting_sandbox" not in body
    assert f"local://accounting_sandbox/draft_bills/{txn_id}" in body
    assert f"local://accounting_sandbox/audit_packets/{txn_id}" in body


# ---------------------------------------------------------------------------
# 14. Writeback page draft bill JSON includes receipt signature
# ---------------------------------------------------------------------------

def test_writeback_page_draft_bill_includes_receipt_signature(client: TestClient):
    txn_id = _full_executed_txn(client)
    client.post(f"/dashboard/transactions/{txn_id}/writeback/accounting-sandbox")
    r = client.get(f"/dashboard/transactions/{txn_id}/writeback/accounting-sandbox")
    assert r.status_code == 200
    assert "receipt_signature" in r.text


# ---------------------------------------------------------------------------
# 15. Audit packet JSON includes checks and receipt
# ---------------------------------------------------------------------------

def test_writeback_page_audit_packet_includes_checks_and_receipt(client: TestClient):
    txn_id = _full_executed_txn(client)
    client.post(f"/dashboard/transactions/{txn_id}/writeback/accounting-sandbox")
    r = client.get(f"/dashboard/transactions/{txn_id}/writeback/accounting-sandbox")
    assert r.status_code == 200
    body = r.text
    assert "checks_json" in body
    assert "receipt_json" in body


# ---------------------------------------------------------------------------
# 16. Existing upload → review → approve → execute → receipt still works
# ---------------------------------------------------------------------------

def test_full_upload_flow_unaffected(client: TestClient, monkeypatch):
    import app.ocr as ocr_mod
    monkeypatch.setattr(
        ocr_mod, "ocr_image_bytes",
        lambda data, **kwargs: {
            "status": "not_available", "engine": "none", "text": None, "notes": [],
        },
    )
    r = client.post("/dashboard/invoices/upload",
                    files={"file": ("inv.png", _MINIMAL_PNG, "image/png")})
    assert r.status_code == 303
    doc_id = r.headers["location"].split("/")[-1]
    r = client.post(f"/dashboard/invoices/review/{doc_id}/submit",
                    data={"invoice_id": "INV-WB-001", "vendor": "Acme Services", "amount": "20000"})
    assert r.status_code == 303
    txn_id = r.headers["location"].split("/")[-1]
    r = client.post(f"/dashboard/transactions/{txn_id}/approve")
    assert r.status_code == 303
    r = client.post(f"/dashboard/transactions/{txn_id}/execute")
    assert r.status_code == 303
    receipt = client.get(f"/dashboard/transactions/{txn_id}/receipt")
    assert receipt.status_code == 200
    assert "receipt_signature" in receipt.text or "Signed payload" in receipt.text


# ---------------------------------------------------------------------------
# 17. Existing demo dashboard flow still works
# ---------------------------------------------------------------------------

def test_demo_flow_unaffected(client: TestClient):
    r = client.post("/dashboard/demo/approval_required")
    assert r.status_code == 303
    txn_id = re.search(r"txn_[a-f0-9]+", r.headers["location"]).group()
    r = client.get(f"/dashboard/transactions/{txn_id}")
    assert r.status_code == 200
    assert "approval required" in r.text.lower()


# ---------------------------------------------------------------------------
# 18. JSON API shapes still unchanged
# ---------------------------------------------------------------------------

def test_json_api_shapes_unchanged(client: TestClient):
    r = client.get("/health")
    assert r.json() == {"status": "ok", "service": "actionrail-finance"}
    r = client.get("/actionrail/manifest.json")
    assert "preflight_action" in r.json()["tools"]


# ---------------------------------------------------------------------------
# Phase 3C — transaction detail UI state polish
# ---------------------------------------------------------------------------

def test_approval_required_shows_request_finance_approval_next_action(client: TestClient):
    r = client.post("/dashboard/demo/approval_required")
    txn_id = re.search(r"txn_[a-f0-9]+", r.headers["location"]).group()
    detail = client.get(f"/dashboard/transactions/{txn_id}")
    body = detail.text
    assert detail.status_code == 200
    assert _next_ui_action_from_detail(body) == "request_finance_approval"
    assert "Finance approval is required before execution." in body


def test_blocked_shows_send_to_human_review_next_action(client: TestClient):
    r = client.post("/dashboard/demo/duplicate_blocked")
    txn_id = re.search(r"txn_[a-f0-9]+", r.headers["location"]).group()
    detail = client.get(f"/dashboard/transactions/{txn_id}")
    body = detail.text
    assert _next_ui_action_from_detail(body) == "send_to_human_review"
    assert "Transaction blocked by policy. Execution is unavailable." in body


def _next_ui_action_from_detail(body: str) -> str | None:
    m = re.search(
        r"Next UI action</div>\s*<div class=\"neo-detail-card__value\"><code>([^<]+)</code>",
        body,
    )
    return m.group(1) if m else None


def test_executed_without_writeback_shows_create_writeback_next_action(client: TestClient):
    txn_id = _full_executed_txn(client)
    detail = client.get(f"/dashboard/transactions/{txn_id}")
    body = detail.text
    assert _next_ui_action_from_detail(body) == "create_accounting_sandbox_writeback"
    assert "Execution complete. A signed receipt exists." in body
    assert "Create Accounting Sandbox Draft Bill" in body
    assert "View Accounting Sandbox Writeback" not in body


def test_executed_with_writeback_shows_view_writeback_next_action(client: TestClient):
    txn_id = _full_executed_txn(client)
    client.post(f"/dashboard/transactions/{txn_id}/writeback/accounting-sandbox")
    detail = client.get(f"/dashboard/transactions/{txn_id}")
    body = detail.text
    assert _next_ui_action_from_detail(body) == "view_accounting_sandbox_writeback"
    assert "Signed receipt and local accounting sandbox writeback are available." in body
    assert "View Accounting Sandbox Writeback" in body
    assert "Create Accounting Sandbox Draft Bill" not in body


def test_approved_shows_execute_action_next_action(client: TestClient):
    r = client.post("/dashboard/demo/approval_required")
    txn_id = re.search(r"txn_[a-f0-9]+", r.headers["location"]).group()
    client.post(f"/dashboard/transactions/{txn_id}/approve")
    detail = client.get(f"/dashboard/transactions/{txn_id}")
    assert _next_ui_action_from_detail(detail.text) == "execute_action"

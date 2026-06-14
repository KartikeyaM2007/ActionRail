from __future__ import annotations

from pathlib import Path

from app.models import InvoiceInput, PreflightRequest
from app.policy import run_preflight, sign_receipt
from app.store import connect, init_db, seed_demo


def fresh_conn(tmp_path: Path):
    conn = connect(tmp_path / "test.db")
    init_db(conn)
    seed_demo(conn)
    return conn


def make_req(**invoice_overrides):
    invoice = {
        "invoice_id": "INV-TEST-1",
        "vendor": "Acme Services",
        "amount": 83000,
        "currency": "INR",
        "invoice_date": "2026-06-13",
        "due_date": "2026-06-25",
        "gst_number": "27ABCDE1234F1Z5",
        "contract_id": "ctr_acme_2026",
        "evidence_urls": ["https://evidence.local/invoices/INV-TEST-1.pdf"],
        "line_items": ["monthly development retainer"],
    }
    invoice.update(invoice_overrides)
    return PreflightRequest(
        agent_id="finance_agent_demo",
        user_id="controller_001",
        intent="pay_invoice",
        action="approve_invoice",
        invoice=InvoiceInput(**invoice),
        constraints={},
    )


def check_map(result):
    return {check.name: check for check in result.checks}


def test_verified_vendor_large_invoice_requires_approval(tmp_path: Path):
    result = run_preflight(fresh_conn(tmp_path), make_req())
    checks = check_map(result)
    assert result.decision == "approval_required"
    assert checks["vendor_verified"].status == "passed"
    assert checks["duplicate_invoice"].status == "passed"
    assert checks["contract_match"].status == "passed"
    assert checks["amount_policy"].status == "warning"


def test_duplicate_invoice_blocks_execution(tmp_path: Path):
    result = run_preflight(fresh_conn(tmp_path), make_req(invoice_id="INV-1045", amount=82000))
    checks = check_map(result)
    assert result.decision == "blocked"
    assert checks["duplicate_invoice"].status == "failed"
    assert "execute_action" in result.blocked_actions


def test_missing_contract_requires_more_evidence(tmp_path: Path):
    result = run_preflight(fresh_conn(tmp_path), make_req(invoice_id="INV-NEW", amount=30000, contract_id=None))
    checks = check_map(result)
    assert result.decision == "needs_more_evidence"
    assert checks["contract_match"].status == "needs_evidence"


def test_unknown_vendor_blocks(tmp_path: Path):
    result = run_preflight(fresh_conn(tmp_path), make_req(invoice_id="INV-UNKNOWN", vendor="Random Vendor", amount=10000, contract_id=None))
    checks = check_map(result)
    assert result.decision == "blocked"
    assert checks["vendor_verified"].status == "failed"


def test_receipt_signature_changes_with_payload():
    one = sign_receipt({"transaction_id": "txn_1", "amount": 1})
    two = sign_receipt({"transaction_id": "txn_1", "amount": 2})
    assert one != two

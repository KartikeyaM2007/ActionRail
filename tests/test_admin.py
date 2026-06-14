"""Phase 5B: admin control plane — vendors, contracts, policy settings."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import InvoiceInput, PreflightRequest
from app.policy import get_transaction, run_preflight
from app.store import connect, get_policy, init_db, list_audit_events, seed_demo, update_policy_settings
from tests.dash_helpers import dash_get, dash_post, extract_csrf, login_as

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

    evidence_dir = tmp_path / "contract_evidence"
    evidence_dir.mkdir()
    monkeypatch.setattr(main, "_CONTRACT_EVIDENCE_DIR", evidence_dir)

    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr(main, "_UPLOAD_DIR", upload_dir)
    yield
    fresh.close()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app, follow_redirects=False)


def _preflight_req(**invoice_overrides):
    invoice = {
        "invoice_id": "INV-ADMIN-001",
        "vendor": "Test Vendor Co",
        "amount": 40000,
        "currency": "INR",
        "invoice_date": "2026-06-14",
        "due_date": "2026-06-30",
        "gst_number": "27TEST1234F1Z5",
        "contract_id": "ctr_test_admin",
        "evidence_urls": ["https://evidence.local/test.pdf"],
        "line_items": ["services"],
    }
    invoice.update(invoice_overrides)
    return PreflightRequest(
        agent_id="admin_test_agent",
        user_id="admin_test",
        intent="pay_invoice",
        action="approve_invoice",
        invoice=InvoiceInput(**invoice),
        constraints={},
    )


def _admin_post(client: TestClient, url: str, *, data: dict | None = None, files: dict | None = None):
    return dash_post(client, url, role="admin", data=data, files=files)


# --- Access control ----------------------------------------------------------


def test_non_admin_cannot_access_admin(client: TestClient):
    r = dash_get(client, "/dashboard/admin", role="viewer")
    assert r.status_code == 403


def test_admin_can_access_admin_dashboard(client: TestClient):
    r = dash_get(client, "/dashboard/admin", role="admin")
    assert r.status_code == 200
    assert "Admin control plane" in r.text


def test_non_admin_access_writes_authorization_denied(client: TestClient):
    from app import main

    before = len(list_audit_events(main.conn))
    dash_get(client, "/dashboard/admin/vendors", role="controller")
    events = list_audit_events(main.conn)
    assert len(events) > before
    assert any(e["action"] == "authorization_denied" for e in events[:5])


# --- Vendors -----------------------------------------------------------------


def test_admin_can_create_vendor(client: TestClient):
    r = _admin_post(
        client,
        "/dashboard/admin/vendors",
        data={
            "name": "Test Vendor Co",
            "gst_number": "27TEST1234F1Z5",
            "country": "IN",
            "status": "verified",
            "risk_level": "low",
            "notes": "admin test",
        },
    )
    assert r.status_code == 303
    assert "/dashboard/admin/vendors/vendor_" in r.headers["location"]


def test_created_verified_vendor_passes_preflight(client: TestClient):
    from app import main
    from app.store import create_contract, create_vendor

    create_vendor(
        main.conn,
        vendor_id="vendor_pv",
        name="Preflight Verified Co",
        gst_number="27PV1234F1Z5",
        country="IN",
        status="verified",
        risk_level="low",
    )
    create_contract(
        main.conn,
        contract_id="ctr_pv",
        vendor_name="Preflight Verified Co",
        max_amount=100000,
        currency="INR",
        start_date="2026-01-01",
        end_date="2027-12-31",
        status="active",
        evidence_url="local://contract_evidence/test",
    )
    result = run_preflight(
        main.conn,
        _preflight_req(
            vendor="Preflight Verified Co",
            invoice_id="INV-PV-1",
            contract_id="ctr_pv",
            amount=40000,
            gst_number="27PV1234F1Z5",
        ),
    )
    checks = {c.name: c for c in result.checks}
    assert checks["vendor_verified"].status == "passed"


def test_pending_vendor_fails_preflight(client: TestClient):
    from app import main
    from app.store import create_vendor

    create_vendor(
        main.conn,
        vendor_id="vendor_pen",
        name="Pending Vendor Co",
        gst_number=None,
        country="IN",
        status="pending_review",
        risk_level="medium",
    )
    result = run_preflight(
        main.conn,
        _preflight_req(vendor="Pending Vendor Co", invoice_id="INV-PEN-1", contract_id=None, amount=5000),
    )
    checks = {c.name: c for c in result.checks}
    assert checks["vendor_verified"].status == "failed"


def test_admin_can_block_vendor(client: TestClient):
    from app import main
    from app.store import create_vendor, get_vendor

    create_vendor(
        main.conn, vendor_id="vendor_blk", name="Block Me Co",
        gst_number=None, country="IN", status="verified", risk_level="low",
    )
    r = _admin_post(
        client,
        "/dashboard/admin/vendors/vendor_blk/update",
        data={"status": "blocked", "risk_level": "high", "country": "IN", "gst_number": ""},
    )
    assert r.status_code == 303
    assert get_vendor(main.conn, "vendor_blk")["status"] == "blocked"


def test_blocked_vendor_fails_preflight(client: TestClient):
    from app import main
    from app.store import create_vendor

    create_vendor(
        main.conn, vendor_id="vendor_blk2", name="Blocked Vendor Co",
        gst_number=None, country="IN", status="blocked", risk_level="high",
    )
    result = run_preflight(
        main.conn,
        _preflight_req(vendor="Blocked Vendor Co", invoice_id="INV-BLK-1", contract_id=None, amount=5000),
    )
    assert result.decision == "blocked"


# --- Contracts ---------------------------------------------------------------


def test_admin_can_create_contract(client: TestClient):
    r = _admin_post(
        client,
        "/dashboard/admin/contracts",
        data={
            "contract_id": "ctr_test_admin",
            "vendor_name": "Acme Services",
            "max_amount": "90000",
            "currency": "INR",
            "start_date": "2026-01-01",
            "end_date": "2027-12-31",
            "status": "active",
        },
    )
    assert r.status_code == 303
    assert r.headers["location"].endswith("/dashboard/admin/contracts/ctr_test_admin")


def test_active_contract_passes_contract_check(client: TestClient):
    from app import main
    from app.store import create_contract, create_vendor

    create_vendor(
        main.conn, vendor_id="vendor_c1", name="Contract Active Co",
        gst_number="27CA1234F1Z5", country="IN", status="verified", risk_level="low",
    )
    create_contract(
        main.conn, contract_id="ctr_active1", vendor_name="Contract Active Co",
        max_amount=50000, currency="INR", start_date="2026-01-01", end_date="2027-12-31",
        status="active", evidence_url="local://x",
    )
    result = run_preflight(
        main.conn,
        _preflight_req(vendor="Contract Active Co", invoice_id="INV-CA-1", contract_id="ctr_active1", amount=30000),
    )
    assert {c.name: c for c in result.checks}["contract_match"].status == "passed"


def test_inactive_contract_fails_contract_check(client: TestClient):
    from app import main
    from app.store import create_contract, create_vendor

    create_vendor(
        main.conn, vendor_id="vendor_c2", name="Contract Inactive Co",
        gst_number="27CI1234F1Z5", country="IN", status="verified", risk_level="low",
    )
    create_contract(
        main.conn, contract_id="ctr_inactive1", vendor_name="Contract Inactive Co",
        max_amount=50000, currency="INR", start_date="2026-01-01", end_date="2027-12-31",
        status="inactive", evidence_url=None,
    )
    result = run_preflight(
        main.conn,
        _preflight_req(vendor="Contract Inactive Co", invoice_id="INV-CI-1", contract_id="ctr_inactive1", amount=30000),
    )
    assert {c.name: c for c in result.checks}["contract_match"].status == "failed"


def test_amount_above_contract_limit_fails(client: TestClient):
    from app import main
    from app.store import create_contract, create_vendor

    create_vendor(
        main.conn, vendor_id="vendor_c3", name="Contract Limit Co",
        gst_number="27CL1234F1Z5", country="IN", status="verified", risk_level="low",
    )
    create_contract(
        main.conn, contract_id="ctr_limit1", vendor_name="Contract Limit Co",
        max_amount=10000, currency="INR", start_date="2026-01-01", end_date="2027-12-31",
        status="active", evidence_url="local://x",
    )
    result = run_preflight(
        main.conn,
        _preflight_req(vendor="Contract Limit Co", invoice_id="INV-CL-1", contract_id="ctr_limit1", amount=50000),
    )
    assert {c.name: c for c in result.checks}["contract_match"].status == "failed"


def test_admin_can_upload_contract_evidence(client: TestClient, tmp_path):
    from app import main
    from app.store import create_contract, list_contract_evidence

    create_contract(
        main.conn, contract_id="ctr_ev1", vendor_name="Acme Services",
        max_amount=50000, currency="INR", start_date="2026-01-01", end_date="2027-12-31",
        status="active", evidence_url=None,
    )
    r = _admin_post(
        client,
        "/dashboard/admin/contracts/ctr_ev1/evidence",
        files={"file": ("contract.pdf", _MINIMAL_PDF, "application/pdf")},
    )
    assert r.status_code == 303
    evidence = list_contract_evidence(main.conn, "ctr_ev1")
    assert len(evidence) == 1
    assert evidence[0]["sha256"]


def test_contract_evidence_gitignored():
    gitignore = Path(__file__).resolve().parent.parent / ".gitignore"
    text = gitignore.read_text(encoding="utf-8")
    assert "data/contract_evidence/*" in text
    assert "!data/contract_evidence/.gitkeep" in text


# --- Policy ------------------------------------------------------------------


def test_admin_can_update_policy_threshold(client: TestClient):
    r = _admin_post(
        client,
        "/dashboard/admin/policies",
        data={
            "approval_threshold": "999999",
            "require_contract_above": "25000",
            "duplicate_window_days": "45",
            "lock_ttl_minutes": "15",
        },
    )
    assert r.status_code == 303
    from app import main
    assert get_policy(main.conn)["approval_threshold"] == 999999


def test_new_threshold_affects_future_preflight(client: TestClient):
    from app import main

    update_policy_settings(main.conn, approval_threshold=999999)
    result = run_preflight(
        main.conn,
        _preflight_req(
            vendor="Acme Services",
            invoice_id="INV-THR-NEW",
            contract_id="ctr_acme_2026",
            amount=83000,
            gst_number="27ABCDE1234F1Z5",
        ),
    )
    checks = {c.name: c for c in result.checks}
    assert checks["amount_policy"].status == "passed"
    assert result.decision == "allow"


def test_policy_update_does_not_mutate_old_transactions(client: TestClient):
    from app import main

    result = run_preflight(
        main.conn,
        _preflight_req(vendor="Acme Services", invoice_id="INV-OLD-1", contract_id="ctr_acme_2026", amount=83000),
    )
    txn_before = get_transaction(main.conn, result.transaction_id)
    update_policy_settings(main.conn, approval_threshold=1)
    txn_after = get_transaction(main.conn, result.transaction_id)
    assert txn_before["decision"] == txn_after["decision"]
    assert txn_before["checks_json"] == txn_after["checks_json"]


# --- Audit + CSRF ------------------------------------------------------------


def test_admin_change_writes_audit_event(client: TestClient):
    from app import main

    r = _admin_post(
        client,
        "/dashboard/admin/vendors",
        data={
            "name": "Audit Vendor Co",
            "status": "pending_review",
            "risk_level": "medium",
            "country": "IN",
        },
    )
    assert r.status_code == 303
    assert any(e["action"] == "vendor_created" for e in list_audit_events(main.conn, limit=20))


def test_missing_csrf_rejects_admin_post(client: TestClient):
    login_as(client, "admin")
    r = client.post(
        "/dashboard/admin/vendors",
        data={"name": "No CSRF", "status": "pending_review", "risk_level": "low", "country": "IN"},
    )
    assert r.status_code == 400


# --- Regression --------------------------------------------------------------

def test_existing_auth_still_works(client: TestClient):
    r = client.get("/login")
    assert r.status_code == 200


def test_json_api_shapes_unchanged(client: TestClient):
    r = client.get("/health")
    assert r.json() == {"status": "ok", "service": "actionrail-finance"}

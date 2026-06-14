"""Phase 5A: local auth, RBAC, CSRF, and audit ledger tests."""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import connect, init_db, list_audit_events, list_audit_events_for_transaction, seed_demo
from tests.dash_helpers import DEMO_CREDENTIALS, dash_get, dash_post, extract_csrf, login_as


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    from app import main, store

    fresh = store.connect(tmp_path / "test.db")
    store.init_db(fresh)
    store.seed_demo(fresh)
    store.update_policy_settings(fresh, require_contract_above=100000)
    monkeypatch.setattr(main, "conn", fresh)
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr(main, "_UPLOAD_DIR", upload_dir)

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
def client() -> TestClient:
    return TestClient(app, follow_redirects=False)


_MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
    b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
    b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _create_txn(client: TestClient) -> str:
    r = dash_post(client, "/dashboard/demo/approval_required", role="controller")
    assert r.status_code == 303
    m = re.search(r"txn_[a-f0-9]+", r.headers["location"])
    assert m
    return m.group()


# --- Login -------------------------------------------------------------------


def test_login_page_loads(client: TestClient):
    r = client.get("/login")
    assert r.status_code == 200
    assert "Sign in" in r.text
    assert 'name="csrf_token"' in r.text


def test_valid_login_succeeds(client: TestClient):
    r = client.get("/login")
    csrf = extract_csrf(r.text)
    email, password = DEMO_CREDENTIALS["viewer"]
    r = client.post("/login", data={"email": email, "password": password, "csrf_token": csrf})
    assert r.status_code == 303
    assert r.headers["location"] == "/dashboard"


def test_invalid_login_fails(client: TestClient):
    r = client.get("/login")
    csrf = extract_csrf(r.text)
    r = client.post(
        "/login",
        data={"email": "viewer@example.local", "password": "wrong", "csrf_token": csrf},
    )
    assert r.status_code == 401
    assert "Invalid email or password" in r.text


def test_dashboard_redirects_to_login_when_unauthenticated(client: TestClient):
    r = client.get("/dashboard")
    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_logged_in_viewer_can_see_dashboard(client: TestClient):
    r = dash_get(client, "/dashboard", role="viewer")
    assert r.status_code == 200
    assert "Signed in as viewer@example.local" in r.text


# --- RBAC --------------------------------------------------------------------


def test_viewer_cannot_approve(client: TestClient):
    txn_id = _create_txn(client)
    login_as(client, "viewer")
    csrf = extract_csrf(dash_get(client, f"/dashboard/transactions/{txn_id}").text)
    r = client.post(
        f"/dashboard/transactions/{txn_id}/approve",
        data={"csrf_token": csrf},
    )
    assert r.status_code == 403
    assert "not allowed" in r.text.lower()


def test_approver_can_approve(client: TestClient):
    txn_id = _create_txn(client)
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/approve", role="approver")
    assert r.status_code == 303


def test_controller_can_upload_review_create_transaction(client: TestClient, monkeypatch):
    import app.ocr as ocr_mod
    monkeypatch.setattr(
        ocr_mod,
        "ocr_image_bytes",
        lambda data, **kwargs: {
            "status": "not_available", "engine": "none", "text": None, "notes": [],
        },
    )
    login_as(client, "controller")
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
        data={"invoice_id": "INV-AUTH-001", "vendor": "Acme Services", "amount": "10000"},
    )
    assert r.status_code == 303
    assert "/dashboard/transactions/txn_" in r.headers["location"]


def test_executor_can_execute_approved_transaction(client: TestClient):
    txn_id = _create_txn(client)
    dash_post(client, f"/dashboard/transactions/{txn_id}/approve", role="approver")
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/execute", role="executor")
    assert r.status_code == 303


def test_executor_can_create_accounting_writeback(client: TestClient):
    txn_id = _create_txn(client)
    dash_post(client, f"/dashboard/transactions/{txn_id}/approve", role="approver")
    dash_post(client, f"/dashboard/transactions/{txn_id}/execute", role="executor")
    r = dash_post(
        client,
        f"/dashboard/transactions/{txn_id}/writeback/accounting-sandbox",
        role="executor",
    )
    assert r.status_code == 303


def test_auditor_can_view_audit_log(client: TestClient):
    r = dash_get(client, "/dashboard/audit", role="auditor")
    assert r.status_code == 200
    assert "Audit log" in r.text


def test_non_auditor_cannot_view_audit_log(client: TestClient):
    r = dash_get(client, "/dashboard/audit", role="viewer")
    assert r.status_code == 403


# --- CSRF --------------------------------------------------------------------


def test_missing_csrf_rejects_dashboard_post(client: TestClient):
    txn_id = _create_txn(client)
    login_as(client, "approver")
    r = client.post(f"/dashboard/transactions/{txn_id}/approve", data={})
    assert r.status_code == 400
    assert "CSRF" in r.text


def test_invalid_csrf_rejects_dashboard_post(client: TestClient):
    txn_id = _create_txn(client)
    login_as(client, "approver")
    r = client.post(
        f"/dashboard/transactions/{txn_id}/approve",
        data={"csrf_token": "not-a-real-token"},
    )
    assert r.status_code == 400
    assert "CSRF" in r.text


# --- Audit events ------------------------------------------------------------


def test_successful_approval_writes_audit_event(client: TestClient):
    from app import main

    txn_id = _create_txn(client)
    dash_post(client, f"/dashboard/transactions/{txn_id}/approve", role="approver")
    events = list_audit_events_for_transaction(main.conn, txn_id)
    actions = [e["action"] for e in events]
    assert "transaction_approved" in actions


def test_successful_execution_writes_audit_event(client: TestClient):
    from app import main

    txn_id = _create_txn(client)
    dash_post(client, f"/dashboard/transactions/{txn_id}/approve", role="approver")
    dash_post(client, f"/dashboard/transactions/{txn_id}/execute", role="executor")
    events = list_audit_events_for_transaction(main.conn, txn_id)
    assert "transaction_executed" in [e["action"] for e in events]


def test_accounting_writeback_writes_audit_event(client: TestClient):
    from app import main

    txn_id = _create_txn(client)
    dash_post(client, f"/dashboard/transactions/{txn_id}/approve", role="approver")
    dash_post(client, f"/dashboard/transactions/{txn_id}/execute", role="executor")
    dash_post(
        client,
        f"/dashboard/transactions/{txn_id}/writeback/accounting-sandbox",
        role="executor",
    )
    events = list_audit_events_for_transaction(main.conn, txn_id)
    actions = [e["action"] for e in events]
    assert "accounting_writeback_created" in actions


def test_transaction_detail_shows_transaction_audit_events(client: TestClient):
    txn_id = _create_txn(client)
    dash_post(client, f"/dashboard/transactions/{txn_id}/approve", role="approver")
    r = dash_get(client, f"/dashboard/transactions/{txn_id}", role="viewer")
    assert r.status_code == 200
    assert "Transaction timeline" in r.text
    assert "transaction_approved" in r.text


# --- Regression --------------------------------------------------------------


def test_json_api_shapes_unchanged(client: TestClient):
    r = client.get("/health")
    assert r.json() == {"status": "ok", "service": "actionrail-finance"}
    r = client.get("/actionrail/manifest.json")
    assert "preflight_action" in r.json()["tools"]
    txn_id = _create_txn(client)
    r = client.post(
        f"/approvals/{txn_id}/approve",
        json={"approver_id": "controller_001", "note": "ok"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["transaction_id"] == txn_id
    assert body["status"] == "approved"


def test_reset_script_resets_users_and_audit_events_idempotently(tmp_path):
    target = tmp_path / "demo.db"
    conn = connect(target)
    init_db(conn)
    seed_demo(conn)
    conn.execute(
        "INSERT INTO audit_events(id, actor_user_id, actor_email, actor_role, action, "
        "target_type, target_id, request_id, event_json, created_at) "
        "VALUES ('aud_test', 'u', 'e@x', 'admin', 'login_success', 'user', 'u', NULL, '{}', '2099')"
    )
    conn.commit()
    conn.close()

    root = Path(__file__).resolve().parent.parent
    spec = importlib.util.spec_from_file_location("reset_demo_db", root / "scripts" / "reset_demo_db.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.reset(db_path=target)
    mod.reset(db_path=target)

    fresh = connect(target)
    assert fresh.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0] == 0
    assert fresh.execute("SELECT COUNT(*) FROM users").fetchone()[0] >= 6
    assert fresh.execute(
        "SELECT 1 FROM users WHERE email='admin@example.local'"
    ).fetchone() is not None
    fresh.close()

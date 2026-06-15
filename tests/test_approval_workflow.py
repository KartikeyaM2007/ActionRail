"""Tests for Phase 5C Approval Workflow Engine."""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.main import app

from app.store import get_approval_workflow_for_transaction, list_approval_steps_for_transaction
from app.policy import get_transaction
from tests.dash_helpers import dash_get, dash_post

TXN_ID_RE = re.compile(r"/dashboard/transactions/(txn_[a-f0-9]+)$")


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    from app import main, store

    fresh = store.connect(tmp_path / "test.db")
    store.init_db(fresh)
    store.seed_demo(fresh)
    monkeypatch.setattr(main, "conn", fresh)
    # Monkey patch tests so we can check DB logic
    global _test_conn
    _test_conn = fresh
    yield
    fresh.close()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app, follow_redirects=False)


def _create(client: TestClient, example_name: str, role: str = "controller") -> str:
    r = dash_post(client, f"/dashboard/demo/{example_name}", role=role)
    assert r.status_code == 303, r.text
    location = r.headers["location"]
    match = TXN_ID_RE.search(location)
    assert match, f"unexpected redirect target: {location}"
    return match.group(1)

def _get_workflow(txn_id: str):
    return get_approval_workflow_for_transaction(_test_conn, txn_id)

def _get_steps(txn_id: str):
    return list_approval_steps_for_transaction(_test_conn, txn_id)

def _get_txn(txn_id: str):
    return get_transaction(_test_conn, txn_id)


# --- Workflow Creation Tests ---

def test_workflow_created_for_approval_required(client: TestClient):
    txn_id = _create(client, "approval_required", role="controller")
    wf = _get_workflow(txn_id)
    assert wf is not None
    assert wf["status"] == "pending"
    assert wf["required_approvals"] == 2
    
def test_workflow_not_created_for_blocked(client: TestClient):
    txn_id = _create(client, "duplicate_blocked", role="controller")
    wf = _get_workflow(txn_id)
    assert wf is None
    
def test_workflow_not_created_for_missing_evidence(client: TestClient):
    txn_id = _create(client, "missing_evidence", role="controller")
    wf = _get_workflow(txn_id)
    assert wf is None

# --- Maker-Checker Tests ---

def test_maker_cannot_approve_own_transaction_as_admin(client: TestClient):
    txn_id = _create(client, "approval_required", role="admin")
    _test_conn.execute("UPDATE transactions SET user_id = 'user_admin' WHERE id = ?", (txn_id,))
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/approve", role="admin")
    assert r.status_code == 403
    assert b"Separation of duties" in r.content

def test_maker_cannot_reject_own_transaction_as_admin(client: TestClient):
    txn_id = _create(client, "approval_required", role="admin")
    _test_conn.execute("UPDATE transactions SET user_id = 'user_admin' WHERE id = ?", (txn_id,))
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/reject", role="admin")
    assert r.status_code == 403
    assert b"Separation of duties" in r.content

def test_different_user_can_approve(client: TestClient):
    txn_id = _create(client, "approval_required", role="controller")
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/approve", role="approver")
    assert r.status_code == 303
    
    wf = _get_workflow(txn_id)
    assert wf["status"] == "pending"
    assert wf["completed_approvals"] == 1

def test_different_user_can_reject(client: TestClient):
    txn_id = _create(client, "approval_required", role="controller")
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/reject", role="approver")
    assert r.status_code == 303
    
    wf = _get_workflow(txn_id)
    assert wf["status"] == "rejected"
    txn = _get_txn(txn_id)
    assert txn["status"] == "rejected"

# --- 1-step vs 2-step Policy Execution ---

def _set_policy(client: TestClient, approval_threshold: float, require_contract_above: float):
    r = dash_post(client, "/dashboard/admin/policies", role="admin", data={
        "approval_threshold": str(approval_threshold),
        "require_contract_above": str(require_contract_above),
        "duplicate_window_days": "30",
        "lock_ttl_minutes": "15"
    })
    assert r.status_code == 303

def test_2_step_workflow_creation(client: TestClient):
    _set_policy(client, 1000, 50000)
    txn_id = _create(client, "approval_required", role="controller")
    wf = _get_workflow(txn_id)
    assert wf["required_approvals"] == 2
    steps = _get_steps(txn_id)
    assert len(steps) == 2
    assert steps[0]["required_role"] == "approver"
    assert steps[1]["required_role"] == "admin"

def test_2_step_workflow_approval_flow(client: TestClient):
    _set_policy(client, 1000, 50000)
    txn_id = _create(client, "approval_required", role="controller")
    
    # Step 1: approver
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/approve", role="approver")
    assert r.status_code == 303
    
    wf = _get_workflow(txn_id)
    assert wf["status"] == "pending"
    assert wf["completed_approvals"] == 1
    
    # Step 2: admin
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/approve", role="admin")
    assert r.status_code == 303
    
    wf = _get_workflow(txn_id)
    assert wf["status"] == "approved"
    assert wf["completed_approvals"] == 2

def test_2_step_workflow_reject_at_step_1(client: TestClient):
    _set_policy(client, 1000, 50000)
    txn_id = _create(client, "approval_required", role="controller")
    
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/reject", role="approver")
    assert r.status_code == 303
    
    wf = _get_workflow(txn_id)
    assert wf["status"] == "rejected"
    assert wf["completed_approvals"] == 0

def test_2_step_workflow_reject_at_step_2(client: TestClient):
    _set_policy(client, 1000, 50000)
    txn_id = _create(client, "approval_required", role="controller")
    
    dash_post(client, f"/dashboard/transactions/{txn_id}/approve", role="approver")
    
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/reject", role="admin")
    assert r.status_code == 303
    
    wf = _get_workflow(txn_id)
    assert wf["status"] == "rejected"
    assert wf["completed_approvals"] == 1

def test_admin_approves_step_1_if_admin(client: TestClient):
    _set_policy(client, 1000, 50000)
    txn_id = _create(client, "approval_required", role="controller")
    
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/approve", role="admin")
    # Admin has "approve_transaction" permission, so it satisfies step 1 and step 2?
    # Wait, our logic says user_role matches `required_role` OR user_role == "admin".
    assert r.status_code == 303
    wf = _get_workflow(txn_id)
    assert wf["completed_approvals"] == 1

# --- Execution Gating ---

def test_execution_blocked_if_workflow_pending(client: TestClient):
    txn_id = _create(client, "approval_required", role="controller")
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/execute", role="executor")
    assert r.status_code == 400
    assert b"Cannot execute: approval workflow is still pending." in r.content

def test_execution_allowed_after_workflow_approved(client: TestClient):
    txn_id = _create(client, "approval_required", role="controller")
    dash_post(client, f"/dashboard/transactions/{txn_id}/approve", role="approver")
    dash_post(client, f"/dashboard/transactions/{txn_id}/approve", role="admin")
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/execute", role="executor")
    assert r.status_code == 303

def test_execution_blocked_if_workflow_rejected(client: TestClient):
    txn_id = _create(client, "approval_required", role="controller")
    dash_post(client, f"/dashboard/transactions/{txn_id}/reject", role="approver")
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/execute", role="executor")
    assert r.status_code == 400

# --- Role enforcement on endpoints ---

def test_executor_cannot_approve(client: TestClient):
    txn_id = _create(client, "approval_required", role="controller")
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/approve", role="executor")
    assert r.status_code == 403

def test_approver_cannot_execute(client: TestClient):
    txn_id = _create(client, "approval_required", role="controller")
    dash_post(client, f"/dashboard/transactions/{txn_id}/approve", role="approver")
    dash_post(client, f"/dashboard/transactions/{txn_id}/approve", role="admin")
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/execute", role="approver")
    assert r.status_code == 403


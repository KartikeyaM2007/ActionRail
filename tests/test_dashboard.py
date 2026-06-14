"""Tests for the operational dashboard routes (Phase 1B)."""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.dash_helpers import dash_get, dash_post

TXN_ID_RE = re.compile(r"/dashboard/transactions/(txn_[a-f0-9]+)$")


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    """Each dashboard test gets a fresh SQLite DB seeded with the demo data.

    `app/main.py` opens its connection at import time bound to `actionrail.db`.
    Without isolation, the persistent intent-lock TTL (15 minutes) makes a
    second demo-preflight of the same invoice land as `decision=blocked`,
    cascading into approve/execute failures. Monkeypatching the module-global
    `conn` ensures every test starts from a deterministic, empty queue.
    """
    from app import main, store

    fresh = store.connect(tmp_path / "test.db")
    store.init_db(fresh)
    store.seed_demo(fresh)
    monkeypatch.setattr(main, "conn", fresh)
    yield
    fresh.close()


@pytest.fixture()
def client() -> TestClient:
    # follow_redirects=False so we can assert 303s and parse Location headers.
    return TestClient(app, follow_redirects=False)


def _create(client: TestClient, example_name: str) -> str:
    r = dash_post(client, f"/dashboard/demo/{example_name}", role="controller")
    assert r.status_code == 303, r.text
    location = r.headers["location"]
    match = TXN_ID_RE.search(location)
    assert match, f"unexpected redirect target: {location}"
    return match.group(1)


def _full_execute(client: TestClient, txn_id: str) -> None:
    dash_post(client, f"/dashboard/transactions/{txn_id}/approve", role="approver")
    dash_post(client, f"/dashboard/transactions/{txn_id}/execute", role="executor")


def _dashboard_stats_from_html(body: str) -> dict[str, int]:
    """Parse stat card values from rendered dashboard HTML."""
    labels = [
        ("total", "Total transactions"),
        ("approval_required", "Approval required"),
        ("needs_evidence", "Needs evidence"),
        ("blocked", "Blocked"),
        ("executed", "Executed"),
    ]
    stats: dict[str, int] = {}
    for key, label in labels:
        m = re.search(
            rf"{re.escape(label)}</div>\s*<div class=\"neo-stat__value\"[^>]*>(\d+)</div>",
            body,
        )
        assert m, f"could not parse stat card: {label}"
        stats[key] = int(m.group(1))
    return stats


# --- Dashboard base ---------------------------------------------------------


def test_dashboard_returns_200_and_demo_section(client: TestClient):
    r = dash_get(client, "/dashboard")
    assert r.status_code == 200
    body = r.text
    assert "RUN DEMO PREFLIGHT".lower() in body.lower()
    assert "/static/neo.css" in body


def test_dashboard_has_needs_evidence_stat_card(client: TestClient):
    r = dash_get(client, "/dashboard")
    assert r.status_code == 200
    body = r.text
    assert "Needs evidence" in body
    # Empty queue → 0 needs_evidence transactions.
    assert "neo-stat--muted" in body
    # After creating a missing-evidence transaction the count should reflect it.
    _create(client, "missing_evidence")
    body = dash_get(client, "/dashboard").text
    # Look for the muted stat card containing "Needs evidence" + "1".
    # The stat-value div holds just the integer.
    assert ">1<" in body  # at least one stat now reads 1


def test_dashboard_table_drops_agent_intent_action_columns(client: TestClient):
    _create(client, "approval_required")
    body = dash_get(client, "/dashboard").text
    # The ">Agent<" / ">Intent<" / ">Action<" header cells are gone.
    assert ">Agent<" not in body
    assert ">Intent<" not in body
    assert ">Action<" not in body
    # Required columns remain.
    for label in ("Transaction", "Vendor", "Amount", "Preflight Decision", "Risk", "Status", "View"):
        assert f">{label}<" in body, f"missing column header: {label}"


def test_dashboard_table_uses_preflight_decision_column(client: TestClient):
    _create(client, "approval_required")
    body = dash_get(client, "/dashboard").text
    assert ">Preflight Decision<" in body
    assert re.search(r"<th[^>]*>Decision</th>", body) is None


def test_dashboard_empty_state_lists_recommended_demo_order(client: TestClient):
    body = dash_get(client, "/dashboard").text
    assert "No transactions yet" in body
    assert "Recommended demo order" in body
    # The three example labels must appear in order in the empty state.
    a = body.find("Approval Required Invoice")
    d = body.find("Duplicate Invoice")
    m = body.find("Missing Evidence Invoice")
    assert 0 <= a < d < m, (a, d, m)


# --- Demo transaction creation ---------------------------------------------


def test_demo_approval_required_creates_transaction(client: TestClient):
    txn_id = _create(client, "approval_required")
    r = dash_get(client, f"/dashboard/transactions/{txn_id}")
    assert r.status_code == 200
    body = r.text
    assert txn_id in body
    assert "approval required" in body.lower()


def test_demo_duplicate_blocked_creates_blocked_transaction(client: TestClient):
    txn_id = _create(client, "duplicate_blocked")
    r = dash_get(client, f"/dashboard/transactions/{txn_id}")
    assert r.status_code == 200
    body = r.text
    assert "blocked" in body.lower()
    assert "duplicate_invoice" in body


def test_demo_missing_evidence_creates_needs_more_evidence(client: TestClient):
    txn_id = _create(client, "missing_evidence")
    r = dash_get(client, f"/dashboard/transactions/{txn_id}")
    assert r.status_code == 200
    body = r.text
    assert "needs more evidence" in body.lower()


def test_invalid_demo_name_returns_404(client: TestClient):
    r = dash_post(client, "/dashboard/demo/not_a_real_example", role="controller")
    assert r.status_code == 404


def test_demo_name_traversal_attempt_is_rejected(client: TestClient):
    # Whitelist must reject anything not in DEMO_EXAMPLES, including path-ish strings.
    r = dash_post(
        client,
        "/dashboard/demo/..%2Fexamples%2Finvoice_approval_required.json",
        role="controller",
    )
    assert r.status_code in (404, 400)


# --- Transaction detail -----------------------------------------------------


def test_detail_shows_decision_and_status(client: TestClient):
    txn_id = _create(client, "approval_required")
    r = dash_get(client, f"/dashboard/transactions/{txn_id}")
    assert r.status_code == 200
    body = r.text
    assert "preflighted" in body.lower()
    assert "Acme Services" in body


def test_detail_404_for_unknown_txn(client: TestClient):
    r = dash_get(client, "/dashboard/transactions/txn_does_not_exist")
    assert r.status_code == 404


# --- Approve / execute / receipt full happy path ---------------------------


def test_full_happy_path_approve_execute_receipt(client: TestClient):
    txn_id = _create(client, "approval_required")

    # Approve
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/approve", role="approver")
    assert r.status_code == 303
    detail = dash_get(client, f"/dashboard/transactions/{txn_id}")
    assert detail.status_code == 200
    assert ">approved<" in detail.text or "neo-badge--status-approved" in detail.text

    # Execute
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/execute", role="executor")
    assert r.status_code == 303
    detail = dash_get(client, f"/dashboard/transactions/{txn_id}")
    assert detail.status_code == 200
    assert "neo-badge--status-executed" in detail.text

    # Receipt
    r = dash_get(client, f"/dashboard/transactions/{txn_id}/receipt")
    assert r.status_code == 200
    assert "receipt_signature" in r.text or "Receipt signature" in r.text
    # Signed payload section is present.
    assert "Signed payload" in r.text


def test_receipt_page_empty_state_when_no_receipt(client: TestClient):
    txn_id = _create(client, "approval_required")
    r = dash_get(client, f"/dashboard/transactions/{txn_id}/receipt")
    assert r.status_code == 200
    assert "No receipt exists for this transaction yet." in r.text


# --- Guardrails -------------------------------------------------------------


def test_blocked_transaction_cannot_execute(client: TestClient):
    txn_id = _create(client, "duplicate_blocked")
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/execute", role="executor")
    # Re-rendered detail with error banner at 400.
    assert r.status_code == 400
    assert b"transaction_blocked" in r.content


def test_rejected_transaction_cannot_execute(client: TestClient):
    txn_id = _create(client, "approval_required")
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/reject", role="approver")
    assert r.status_code == 303
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/execute", role="executor")
    assert r.status_code == 400
    assert b"transaction_rejected" in r.content


def test_needs_more_evidence_cannot_execute(client: TestClient):
    txn_id = _create(client, "missing_evidence")
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/execute", role="executor")
    assert r.status_code == 400
    # decision is needs_more_evidence; status is preflighted (not approved), so the
    # approval-required guard fires first. Either error string is acceptable proof
    # the transaction was blocked from executing.
    assert (
        b"missing_evidence_blocks_execution" in r.content
        or b"approval_required_before_execution" in r.content
    )


def test_blocked_transaction_cannot_be_approved(client: TestClient):
    txn_id = _create(client, "duplicate_blocked")
    r = dash_post(client, f"/dashboard/transactions/{txn_id}/approve", role="approver")
    assert r.status_code == 400
    assert b"blocked_transaction_cannot_be_approved" in r.content


# --- API JSON shape preservation -------------------------------------------


def test_existing_api_endpoints_still_return_json(client: TestClient):
    """Phase 1B refactor must not change the JSON API response shape."""
    # /health
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "actionrail-finance"}
    # /actionrail/manifest.json
    r = client.get("/actionrail/manifest.json")
    assert r.status_code == 200
    j = r.json()
    assert j["name"] == "ActionRail Finance"
    assert "preflight_action" in j["tools"]
    # JSON approve route still returns JSON shape with transaction_id / status / approval.
    txn_id = _create(client, "approval_required")
    r = client.post(
        f"/approvals/{txn_id}/approve",
        json={"approver_id": "controller_001", "note": "ok"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["transaction_id"] == txn_id
    assert body["status"] == "approved"
    assert body["approval"]["approver_id"] == "controller_001"


# --- Dashboard stat correctness (Phase 3D) ----------------------------------


def test_compute_dashboard_stats_executed_not_approval_required():
    from app.main import _compute_dashboard_stats

    counts = [
        {"decision": "approval_required", "status": "executed", "n": 1},
    ]
    stats = _compute_dashboard_stats(counts)
    assert stats == {
        "total": 1,
        "approval_required": 0,
        "needs_evidence": 0,
        "blocked": 0,
        "executed": 1,
    }


def test_compute_dashboard_stats_preflighted_approval_required():
    from app.main import _compute_dashboard_stats

    counts = [
        {"decision": "approval_required", "status": "preflighted", "n": 1},
    ]
    stats = _compute_dashboard_stats(counts)
    assert stats["approval_required"] == 1
    assert stats["executed"] == 0


def test_compute_dashboard_stats_blocked():
    from app.main import _compute_dashboard_stats

    counts = [
        {"decision": "blocked", "status": "blocked", "n": 1},
    ]
    stats = _compute_dashboard_stats(counts)
    assert stats["blocked"] == 1


def test_compute_dashboard_stats_needs_evidence():
    from app.main import _compute_dashboard_stats

    counts = [
        {"decision": "needs_more_evidence", "status": "preflighted", "n": 1},
    ]
    stats = _compute_dashboard_stats(counts)
    assert stats["needs_evidence"] == 1


def test_compute_dashboard_stats_needs_evidence_excludes_executed():
    from app.main import _compute_dashboard_stats

    counts = [
        {"decision": "needs_more_evidence", "status": "executed", "n": 1},
    ]
    stats = _compute_dashboard_stats(counts)
    assert stats["needs_evidence"] == 0


def test_dashboard_stats_after_execute(client: TestClient):
    txn_id = _create(client, "approval_required")
    body = _dashboard_stats_from_html(dash_get(client, "/dashboard").text)
    assert body["approval_required"] == 1
    assert body["executed"] == 0

    _full_execute(client, txn_id)
    body = _dashboard_stats_from_html(dash_get(client, "/dashboard").text)
    assert body["total"] == 1
    assert body["approval_required"] == 0
    assert body["executed"] == 1


def test_dashboard_stats_blocked_increments_blocked(client: TestClient):
    _create(client, "duplicate_blocked")
    body = _dashboard_stats_from_html(dash_get(client, "/dashboard").text)
    assert body["blocked"] == 1
    assert body["approval_required"] == 0


def test_dashboard_stats_missing_evidence_increments_needs_evidence(client: TestClient):
    _create(client, "missing_evidence")
    body = _dashboard_stats_from_html(dash_get(client, "/dashboard").text)
    assert body["needs_evidence"] == 1
    assert body["executed"] == 0

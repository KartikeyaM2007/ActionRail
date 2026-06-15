import json
import os
import pytest
import sqlite3
from fastapi.testclient import TestClient
from unittest import mock

from app.main import app
from app.store import connect

@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    from app import main, store, api_security

    fresh = store.connect(tmp_path / "test.db")
    store.init_db(fresh)
    store.seed_demo(fresh)
    monkeypatch.setattr(main, "conn", fresh)
    monkeypatch.setattr(api_security, "connect", lambda *args, **kwargs: store.connect(tmp_path / "test.db"))
    yield fresh
    fresh.close()


@pytest.fixture
def client(_isolated_db):
    # Set env var to enable API security during test
    os.environ["ACTIONRAIL_REQUIRE_API_KEY"] = "1"
    
    with TestClient(app) as c:
        yield c
        
    del os.environ["ACTIONRAIL_REQUIRE_API_KEY"]


@pytest.fixture
def seed_test_data(_isolated_db):
    conn = _isolated_db
    # Add a test client without rate limits that can quickly hit endpoints if needed
    import hashlib
    key_hash = hashlib.pbkdf2_hmac("sha256", b"sk_test_test_secret", b"actionrail", 100000).hex()
    conn.execute(
        """
        INSERT INTO api_clients (
            id, name, client_key_hash, client_key_prefix, role,
            allowed_scopes_json, rate_limit_per_minute, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "client_test", "Test Agent", key_hash, "sk_test", "agent",
            json.dumps(["preflight:create", "transactions:read", "receipts:read"]),
            100, "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"
        )
    )
    conn.commit()


def test_api_security_missing_key(client, seed_test_data):
    response = client.post("/actions/preflight", json={
        "agent_id": "test_agent", "action": "pay_invoice",
        "parameters": {"vendor_id": "vendor_acme", "amount": 100, "currency": "INR", "invoice_number": "INV-100"}
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "missing_api_key"


def test_api_security_invalid_key(client, seed_test_data):
    response = client.get("/transactions", headers={"X-ActionRail-API-Key": "sk_test_wrongsecret"})
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_api_key"


def test_api_security_valid_key(client, seed_test_data):
    response = client.get("/transactions", headers={"X-ActionRail-API-Key": "sk_test_test_secret"})
    assert response.status_code == 200
    assert "transactions" in response.json()


def test_api_security_scope_denied(client, seed_test_data, _isolated_db):
    # Change test client to NOT have preflight scope
    conn = _isolated_db
    conn.execute("UPDATE api_clients SET allowed_scopes_json='[\"transactions:read\"]' WHERE id='client_test'")
    conn.commit()

    response = client.post("/actions/preflight", headers={"X-ActionRail-API-Key": "sk_test_test_secret"}, json={
        "agent_id": "test_agent", "user_id": "user_demo", "intent": "Pay vendor", "action": "pay_invoice",
        "invoice": {"vendor": "vendor_acme", "amount": 100, "currency": "INR", "invoice_id": "INV-100"}
    })
    assert response.status_code == 403
    assert response.json()["detail"] == "scope_denied"


def test_api_security_rate_limited(client, seed_test_data, _isolated_db):
    # Set limit to 1
    conn = _isolated_db
    conn.execute("UPDATE api_clients SET rate_limit_per_minute=1 WHERE id='client_test'")
    conn.commit()

    # Request 1 (Success)
    resp1 = client.get("/transactions", headers={"X-ActionRail-API-Key": "sk_test_test_secret"})
    assert resp1.status_code == 200
    
    # Request 2 (Rate Limited)
    resp2 = client.get("/transactions", headers={"X-ActionRail-API-Key": "sk_test_test_secret"})
    assert resp2.status_code == 429
    assert resp2.json()["detail"] == "rate_limit_exceeded"


def test_api_security_idempotency_success(client, seed_test_data):
    payload = {
        "agent_id": "test_agent", "user_id": "user_demo", "intent": "Pay vendor", "action": "pay_invoice",
        "invoice": {"vendor": "vendor_acme", "amount": 100, "currency": "INR", "invoice_id": "INV-100"}
    }
    headers = {
        "X-ActionRail-API-Key": "sk_test_test_secret",
        "Idempotency-Key": "idem_123"
    }
    
    # Request 1
    resp1 = client.post("/actions/preflight", headers=headers, json=payload)
    assert resp1.status_code == 200
    
    # Request 2 (Replayed)
    resp2 = client.post("/actions/preflight", headers=headers, json=payload)
    assert resp2.status_code == 200
    assert resp1.json() == resp2.json()


def test_api_security_idempotency_conflict(client, seed_test_data):
    payload1 = {
        "agent_id": "test_agent", "user_id": "user_demo", "intent": "Pay vendor", "action": "pay_invoice",
        "invoice": {"vendor": "vendor_acme", "amount": 100, "currency": "INR", "invoice_id": "INV-100"}
    }
    payload2 = {
        "agent_id": "test_agent", "user_id": "user_demo", "intent": "Pay vendor", "action": "pay_invoice",
        "invoice": {"vendor": "vendor_acme", "amount": 200, "currency": "INR", "invoice_id": "INV-101"}
    }
    headers = {
        "X-ActionRail-API-Key": "sk_test_test_secret",
        "Idempotency-Key": "idem_456"
    }
    
    # Request 1
    resp1 = client.post("/actions/preflight", headers=headers, json=payload1)
    assert resp1.status_code == 200
    
    # Request 2 (Different payload, same key)
    resp2 = client.post("/actions/preflight", headers=headers, json=payload2)
    assert resp2.status_code == 409
    assert resp2.json()["detail"] == "idempotency_conflict"

def test_api_security_disabled_client(client, seed_test_data, _isolated_db):
    conn = _isolated_db
    conn.execute("UPDATE api_clients SET is_active=0 WHERE id='client_test'")
    conn.commit()

    response = client.get("/transactions", headers={"X-ActionRail-API-Key": "sk_test_test_secret"})
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_api_key"

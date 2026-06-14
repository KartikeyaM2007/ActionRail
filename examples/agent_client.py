#!/usr/bin/env python3
"""
ActionRail Finance — Agent Client Example
Demonstrates how an AI agent calls ActionRail using only the Python Standard Library.
"""

import json
import urllib.request
import urllib.error
import uuid

class ActionRailClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _request(self, method: str, path: str, payload: dict | None = None, idempotency_key: str | None = None) -> dict:
        url = f"{self.base_url}{path}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if self.api_key:
            headers["X-ActionRail-API-Key"] = self.api_key
            
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
            
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            try:
                err_json = json.loads(err_body)
                raise Exception(f"ActionRail HTTP {e.code}: {err_json.get('detail', err_body)}")
            except json.JSONDecodeError:
                raise Exception(f"ActionRail HTTP {e.code}: {err_body}")
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Failed to connect to ActionRail at {self.base_url}. "
                f"Reason: {e.reason}. Is the ActionRail server running?"
            )

    def preflight_action(self, action_request: dict, idempotency_key: str | None = None) -> dict:
        """Submit a finance action preflight."""
        return self._request("POST", "/actions/preflight", payload=action_request, idempotency_key=idempotency_key)

    def get_transaction(self, transaction_id: str) -> dict:
        """Get transaction details."""
        return self._request("GET", f"/transactions/{transaction_id}")

    def get_receipt(self, transaction_id: str) -> dict:
        """Get execution receipt."""
        return self._request("GET", f"/receipts/{transaction_id}")

    def execute_transaction(self, transaction_id: str) -> dict:
        """Execute transaction once allowed or approved."""
        return self._request("POST", f"/actions/{transaction_id}/execute")


def run_demo():
    # Placeholder API Key - replace with a real client key created in the Admin UI
    # when ACTIONRAIL_REQUIRE_API_KEY environment variable is enabled.
    api_key = "<local-demo-agent-key>"
    
    client = ActionRailClient(base_url="http://127.0.0.1:8000", api_key=api_key)
    
    # Preflight Request Payload matching app/models.py PreflightRequest schema
    payload = {
        "agent_id": "agent_billing_01",
        "user_id": "controller@example.local",
        "intent": "Pay vendor invoice after verification",
        "action": "pay_invoice",
        "invoice": {
            "invoice_id": "INV-2026-900",
            "vendor": "Acme Services",
            "amount": 83000,
            "currency": "INR",
            "invoice_date": "2026-06-01",
            "due_date": "2026-07-01",
            "gst_number": "27AAAAA1111A1Z1"
        }
    }
    
    # 1. Generate unique idempotency key for this attempt
    idempotency_key = f"idem_{uuid.uuid4().hex[:12]}"
    
    print("=== Submitting Preflight Request to ActionRail ===")
    print(f"Idempotency Key: {idempotency_key}")
    print(f"Invoice: {payload['invoice']['vendor']} - {payload['invoice']['amount']} {payload['invoice']['currency']}")
    
    try:
        # Check preflight
        result = client.preflight_action(payload, idempotency_key=idempotency_key)
        txn_id = result.get("transaction_id")
        decision = result.get("decision")
        
        print("\n=== ActionRail Response ===")
        print(f"Transaction ID: {txn_id}")
        print(f"Decision: {decision}")
        print(f"Risk Evaluation: {result.get('risk')}")
        
        # 2. Decision Handling Logic
        if decision == "allow":
            print("[Action] Decision: ALLOWED. Safe to proceed only through controlled route.")
            print("Executing simulated transaction...")
            exec_res = client.execute_transaction(txn_id)
            print(f"Execution Status: {exec_res.get('status')}")
            
            # Fetch receipt
            receipt = client.get_receipt(txn_id)
            print(f"HMAC Signed Receipt Signature: {receipt.get('receipt_signature')}")
            
        elif decision == "approval_required":
            print("[Action] Decision: APPROVAL_REQUIRED. Waiting for human approval.")
            print(f"Next Allowed Action: {result.get('allowed_next_action')}")
            print(f"Human must sign-off on the dashboard at: http://127.0.0.1:8000/dashboard/transactions/{txn_id}")
            
        elif decision == "needs_more_evidence":
            print("[Action] Decision: NEEDS_MORE_EVIDENCE. Ask for more evidence.")
            print("Missing details:", [c["message"] for c in result.get("checks", []) if c["status"] == "needs_evidence"])
            
        elif decision == "blocked":
            print("[Action] Decision: BLOCKED. Do not execute!")
            print("Reason:", [c["message"] for c in result.get("checks", []) if c["status"] == "failed"])
            
    except ConnectionError as e:
        print(f"\n[Warning] {e}")
        print("\nTo run this locally:")
        print("1. Start ActionRail: uvicorn app.main:app --reload")
        print("2. Re-run this example: python examples/agent_client.py")
    except Exception as e:
        print(f"\n[Error] {e}")

if __name__ == "__main__":
    run_demo()

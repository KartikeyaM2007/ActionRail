"""
ActionRail Finance — LangGraph-style Tool Integration Example
This demonstrates how an agent framework (like LangGraph or LangChain) exposes 
ActionRail's preflight check as a tool/node in a financial agentic workflow.

This example is dependency-free and can be run or imported directly.
"""

import json
import os
import urllib.request
import urllib.error

# In a real LangGraph setup, you would use @tool decoration:
# from langchain_core.tools import tool
# @tool

def request_finance_action_preflight(
    agent_id: str,
    user_id: str,
    intent: str,
    action: str,
    invoice_id: str,
    vendor: str,
    amount: float,
    currency: str,
    due_date: str,
    invoice_date: str | None = None,
    gst_number: str | None = None,
    contract_id: str | None = None,
    evidence_refs: list[str] | None = None,
    idempotency_key: str | None = None,
    base_url: str = "http://127.0.0.1:8000"
) -> dict:
    """
    Submits a financial transaction request to ActionRail for preflight policy verification.
    
    Before attempting any finance action (like creating or paying an invoice), call this tool.
    It returns a deterministic policy decision:
      - 'allow': Safe to proceed. Call the execution tool.
      - 'approval_required': HUMAN sign-off needed. Stop the workflow and wait for approval.
      - 'blocked': Policy check failed. Abort the action.
      - 'needs_more_evidence': Evidence or details missing. Find and attach evidence.
    """
    
    payload = {
        "agent_id": agent_id,
        "user_id": user_id,
        "intent": intent,
        "action": action,
        "invoice": {
            "invoice_id": invoice_id,
            "vendor": vendor,
            "amount": amount,
            "currency": currency,
            "due_date": due_date,
            "invoice_date": invoice_date,
            "gst_number": gst_number,
            "contract_id": contract_id,
            "evidence_urls": evidence_refs or []
        }
    }
    
    # Retrieve api key from environment if configured
    api_key = os.environ.get("ACTIONRAIL_API_KEY")
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    if api_key:
        headers["X-ActionRail-API-Key"] = api_key
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
        
    url = f"{base_url.rstrip('/')}/actions/preflight"
    data = json.dumps(payload).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return {"error": True, "detail": json.loads(err_body).get("detail", err_body)}
        except json.JSONDecodeError:
            return {"error": True, "detail": err_body}
    except urllib.error.URLError as e:
        # Fallback for offline demo: simulate the API shape if ActionRail is not running
        return {
            "transaction_id": "sim_txn_offline_example",
            "decision": "approval_required",
            "risk": "medium",
            "allowed_next_action": "request_finance_approval",
            "checks": [
                {"check_name": "vendor_verified", "status": "passed", "message": "Vendor exists in registry"},
                {"check_name": "amount_policy", "status": "warning", "message": "Invoice exceeds single-agent threshold; needs approval"}
            ],
            "notes": "ActionRail server offline. Returned offline simulation for local testing."
        }


# =====================================================================
# LangGraph Workflow Node Demonstration (Pseudo-code)
# =====================================================================
"""
How to integrate this tool in a LangGraph StateGraph:

from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END

# 1. Define Agent State
class AgentState(TypedDict):
    invoice_payload: dict
    preflight_result: dict
    status: str
    receipt: dict
    errors: list[str]

# 2. Preflight Node
def check_preflight_node(state: AgentState):
    payload = state["invoice_payload"]
    res = request_finance_action_preflight(
        agent_id="my_finance_agent",
        user_id="controller@example.local",
        intent="Process monthly SaaS renewal",
        action="pay_invoice",
        invoice_id=payload["invoice_id"],
        vendor=payload["vendor"],
        amount=payload["amount"],
        currency=payload["currency"],
        due_date=payload["due_date"],
        idempotency_key=payload.get("idempotency_key")
    )
    return {"preflight_result": res}

# 3. Router Edge Logic
def route_decision(state: AgentState):
    decision = state["preflight_result"].get("decision")
    if decision == "allow":
        return "execute_payment"
    elif decision == "approval_required":
        return "wait_for_human"
    elif decision == "needs_more_evidence":
        return "collect_more_evidence"
    else:
        return "abort_workflow"

# 4. Build Graph
workflow = StateGraph(AgentState)
workflow.add_node("preflight", check_preflight_node)
workflow.add_node("execute_payment", execute_payment_node)
workflow.add_node("wait_for_human", wait_for_human_node)
workflow.add_node("collect_more_evidence", collect_evidence_node)
workflow.add_node("abort_workflow", abort_workflow_node)

workflow.set_entry_point("preflight")
workflow.add_conditional_edges("preflight", route_decision)
...
"""

if __name__ == "__main__":
    # Test execution when run directly
    print("Running LangGraph tool offline validation...")
    res = request_finance_action_preflight(
        agent_id="test_langgraph_agent",
        user_id="controller@example.local",
        intent="Renew software contract",
        action="pay_invoice",
        invoice_id="INV-9999",
        vendor="Acme Corp",
        amount=150000.0,
        currency="INR",
        due_date="2026-07-01"
    )
    print("\nResult payload:")
    print(json.dumps(res, indent=2))

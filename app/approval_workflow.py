from __future__ import annotations

import uuid
from typing import Any


def plan_approval_workflow(transaction: dict[str, Any], policy_settings: dict[str, Any] | None = None) -> dict[str, Any] | None:
    if transaction.get("decision") != "approval_required":
        return None

    if transaction.get("status") in {"blocked", "rejected", "executed"}:
        return None

    policy = policy_settings or {}
    approval_threshold = float(policy.get("approval_threshold", 50000))
    require_contract_above = float(policy.get("require_contract_above", 25000))

    invoice = transaction.get("invoice") or transaction.get("invoice_json") or {}
    amount = invoice.get("amount")
    risk = transaction.get("risk", "low")

    # Determine workflow requirements
    two_step = False
    reason = "approval required by policy"

    if amount is None:
        two_step = False
        reason = "missing amount requires approval"
    elif risk == "high":
        two_step = True
        reason = "high risk requires approver and admin"
    elif amount >= require_contract_above:
        two_step = True
        reason = "amount exceeds contract evidence threshold"
    elif amount >= approval_threshold:
        two_step = False
        reason = "medium risk above approval threshold"

    # Generate workflow and steps definition (not stored in DB yet, returned to caller)
    workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
    
    steps = []
    
    if two_step:
        steps.append({
            "step_id": f"stp_{uuid.uuid4().hex[:12]}",
            "step_order": 1,
            "required_role": "approver"
        })
        steps.append({
            "step_id": f"stp_{uuid.uuid4().hex[:12]}",
            "step_order": 2,
            "required_role": "admin"
        })
    else:
        steps.append({
            "step_id": f"stp_{uuid.uuid4().hex[:12]}",
            "step_order": 1,
            "required_role": "approver"
        })

    return {
        "workflow_id": workflow_id,
        "workflow_type": "two_step" if two_step else "one_step",
        "required_approvals": len(steps),
        "reason": reason,
        "steps": steps
    }


def enforce_maker_checker(current_user: dict[str, Any], transaction: dict[str, Any]) -> bool:
    """
    Return True if maker-checker passes (user is NOT the creator).
    Return False if maker-checker fails (user IS the creator).
    """
    # If transaction has no user_id, allow.
    txn_user_id = transaction.get("user_id")
    if not txn_user_id:
        return True
        
    if current_user["id"] == txn_user_id:
        return False
        
    return True

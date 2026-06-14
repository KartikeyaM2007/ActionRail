import json
from typing import Any

from app.models import CheckResult, InvoiceInput, PreflightRequest
from app.policy import (
    check_amount_policy,
    check_contract,
    check_duplicate,
    check_evidence,
    check_vendor,
    decide,
    get_transaction,
)
from app.store import get_policy, loads

def compare_original_to_current_policy(replay: dict[str, Any]) -> list[str]:
    """Calculate and summarize differences between original and current policy outcomes."""
    orig = replay["original_state"]
    curr = replay["current_state"]
    diffs = []

    if orig["decision"] == curr["decision"] and orig["risk"] == curr["risk"]:
        # We need to dig deeper into checks to see if anything changed.
        pass
    elif orig["decision"] != curr["decision"]:
        if curr["decision"] == "blocked" and orig["decision"] != "blocked":
            diffs.append("policy_now_stricter")
        elif orig["decision"] == "blocked" and curr["decision"] != "blocked":
            diffs.append("policy_now_looser")
        else:
            diffs.append(f"decision_changed_from_{orig['decision']}_to_{curr['decision']}")

    orig_checks = {c["name"]: c for c in orig["checks"]}
    curr_checks = {c["name"]: c for c in curr["checks"]}

    for name in ["vendor_verified", "contract_match", "duplicate_invoice", "amount_policy", "evidence_attached"]:
        c_orig = orig_checks.get(name, {})
        c_curr = curr_checks.get(name, {})
        if c_orig.get("status") != c_curr.get("status"):
            if name == "vendor_verified":
                diffs.append("vendor_status_changed")
            elif name == "contract_match":
                diffs.append("contract_status_changed")
            elif name == "duplicate_invoice":
                diffs.append("duplicate_detection_changed")
            elif name == "amount_policy":
                diffs.append("amount_policy_changed")

    if not diffs:
        diffs.append("unchanged")
    return diffs

def build_transaction_replay(conn, transaction_id: str) -> dict[str, Any]:
    txn = get_transaction(conn, transaction_id)
    if not txn:
        raise ValueError("Transaction not found")

    invoice_dict = txn.get("invoice_json", {})
    invoice = InvoiceInput(**invoice_dict)

    req = PreflightRequest(
        agent_id=txn["agent_id"],
        user_id=txn["user_id"],
        intent=txn["intent"],
        action=txn["action"],
        invoice=invoice,
        constraints=loads(txn.get("constraints_json"), {})
    )

    policy = get_policy(conn)
    allowed_actions = set(policy.get("allowed_actions", []))

    checks: list[CheckResult] = []
    if allowed_actions and req.action not in allowed_actions:
        checks.append(
            CheckResult(
                name="action_allowed",
                status="failed",
                message="Action is not allowed by finance policy.",
                evidence={"action": req.action, "allowed_actions": sorted(allowed_actions)},
            )
        )
    else:
        checks.append(
            CheckResult(
                name="action_allowed",
                status="passed",
                message="Action is recognized by finance policy.",
                evidence={"action": req.action},
            )
        )

    # Note: We do not call check_intent_lock here to avoid DB mutation during a replay.
    checks.extend([
        check_vendor(conn, req),
        check_duplicate(conn, req, policy),
        check_contract(conn, req, policy),
        check_amount_policy(req, policy),
        check_evidence(req)
    ])

    # Spoof intent lock for replay to keep shapes identical
    checks.append(
        CheckResult(
            name="intent_lock",
            status="passed",
            message="Intent lock granted for this invoice action (simulated).",
            evidence={"lock_key": "replay_simulation"}
        )
    )

    decision, risk, next_action, blocked_actions = decide(checks, req, policy)

    replay = {
        "transaction_id": transaction_id,
        "original_state": {
            "decision": txn["decision"],
            "risk": txn["risk"],
            "checks": txn.get("checks_json", [])
        },
        "current_state": {
            "decision": decision,
            "risk": risk,
            "checks": [c.model_dump() for c in checks]
        },
        "original_decision": txn["decision"],
        "replay_decision": decision,
    }
    replay["differences"] = compare_original_to_current_policy(replay)
    replay["policy_changed"] = len([d for d in replay["differences"] if d != "unchanged"]) > 0
    return replay

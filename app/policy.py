from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import timedelta
from typing import Any

from app.models import CheckResult, PreflightRequest, PreflightResponse
from app.store import cleanup_expired_locks, dumps, get_policy, loads, lock_expires_at, utc_now

RECEIPT_SECRET = b"dev-actionrail-secret-change-me"


def transaction_id() -> str:
    return f"txn_{uuid.uuid4().hex[:12]}"


def receipt_id() -> str:
    return f"rcpt_{uuid.uuid4().hex[:12]}"


def invoice_lock_key(req: PreflightRequest) -> str:
    invoice = req.invoice
    return f"{req.intent}:{req.action}:{invoice.vendor.lower()}:{invoice.invoice_id.lower()}"


def check_vendor(conn, req: PreflightRequest) -> CheckResult:
    row = conn.execute("SELECT * FROM vendors WHERE lower(name)=lower(?)", (req.invoice.vendor,)).fetchone()
    if not row:
        return CheckResult(
            name="vendor_verified",
            status="failed",
            message="Vendor is not known or verified.",
            evidence={"vendor": req.invoice.vendor},
        )
    vendor = dict(row)
    status = vendor.get("status") or ("verified" if vendor.get("verified") else "pending_review")
    if status == "blocked":
        return CheckResult(
            name="vendor_verified",
            status="failed",
            message="Vendor is blocked.",
            evidence={"vendor": vendor["name"], "status": status},
        )
    if status != "verified":
        return CheckResult(
            name="vendor_verified",
            status="failed",
            message="Vendor exists but is not verified.",
            evidence={"vendor": vendor["name"], "status": status, "risk_level": vendor["risk_level"]},
        )
    gst_match = True
    if req.invoice.gst_number and vendor["gst_number"]:
        gst_match = req.invoice.gst_number == vendor["gst_number"]
    if not gst_match:
        return CheckResult(
            name="vendor_verified",
            status="warning",
            message="Vendor is verified, but GST number does not match stored vendor record.",
            evidence={"expected_gst": vendor["gst_number"], "received_gst": req.invoice.gst_number},
        )
    return CheckResult(
        name="vendor_verified",
        status="passed",
        message="Vendor is verified.",
        evidence={"vendor": vendor["name"], "gst_number": vendor["gst_number"]},
    )


def check_duplicate(conn, req: PreflightRequest, policy: dict[str, Any]) -> CheckResult:
    window_days = int(policy.get("duplicate_window_days", 45))
    since = (utc_now() - timedelta(days=window_days)).isoformat()
    rows = conn.execute(
        """
        SELECT invoice_id, vendor, amount, status, created_at
        FROM invoices
        WHERE lower(vendor)=lower(?)
          AND amount=?
          AND invoice_id != ?
          AND created_at >= ?
        ORDER BY created_at DESC
        LIMIT 5
        """,
        (req.invoice.vendor, req.invoice.amount, req.invoice.invoice_id, since),
    ).fetchall()
    if rows:
        return CheckResult(
            name="duplicate_invoice",
            status="failed",
            message="Possible duplicate invoice found with same vendor and amount.",
            evidence={"matches": [dict(row) for row in rows]},
        )
    return CheckResult(
        name="duplicate_invoice",
        status="passed",
        message="No duplicate invoice found inside policy window.",
        evidence={"window_days": window_days},
    )


def check_contract(conn, req: PreflightRequest, policy: dict[str, Any]) -> CheckResult:
    require_contract_above = float(policy.get("require_contract_above", 25000))
    if req.invoice.amount < require_contract_above and not req.invoice.contract_id:
        return CheckResult(
            name="contract_match",
            status="passed",
            message="Invoice amount is below contract evidence threshold.",
            evidence={"threshold": require_contract_above},
        )
    if not req.invoice.contract_id:
        return CheckResult(
            name="contract_match",
            status="needs_evidence",
            message="Contract evidence is required for this invoice amount.",
            evidence={"threshold": require_contract_above, "amount": req.invoice.amount},
        )
    row = conn.execute("SELECT * FROM contracts WHERE id=?", (req.invoice.contract_id,)).fetchone()
    if not row:
        return CheckResult(
            name="contract_match",
            status="failed",
            message="Contract is missing or inactive.",
            evidence={"contract_id": req.invoice.contract_id},
        )
    contract = dict(row)
    status = contract.get("status") or ("active" if contract.get("active") else "inactive")
    if status != "active":
        return CheckResult(
            name="contract_match",
            status="failed",
            message="Contract is missing or inactive.",
            evidence={"contract_id": req.invoice.contract_id, "status": status},
        )
    end_date = contract.get("end_date")
    if end_date:
        try:
            from datetime import date
            if date.fromisoformat(str(end_date)[:10]) < utc_now().date():
                return CheckResult(
                    name="contract_match",
                    status="failed",
                    message="Contract has expired.",
                    evidence={"contract_id": req.invoice.contract_id, "end_date": end_date},
                )
        except ValueError:
            pass
    if contract["vendor_name"].lower() != req.invoice.vendor.lower():
        return CheckResult(
            name="contract_match",
            status="failed",
            message="Contract vendor does not match invoice vendor.",
            evidence={"contract_vendor": contract["vendor_name"], "invoice_vendor": req.invoice.vendor},
        )
    if contract["max_amount"] is not None and req.invoice.amount > float(contract["max_amount"]):
        return CheckResult(
            name="contract_match",
            status="failed",
            message="Invoice amount exceeds contract limit.",
            evidence={"contract_limit": contract["max_amount"], "amount": req.invoice.amount},
        )
    return CheckResult(
        name="contract_match",
        status="passed",
        message="Invoice matches active contract.",
        evidence={
            "contract_id": contract["id"],
            "contract_limit": contract["max_amount"],
            "evidence_url": contract["evidence_url"],
        },
    )


def check_amount_policy(req: PreflightRequest, policy: dict[str, Any]) -> CheckResult:
    approval_threshold = float(policy.get("approval_threshold", 50000))
    critical_threshold = float(policy.get("critical_threshold", 250000))
    amount = req.invoice.amount
    if amount >= critical_threshold:
        return CheckResult(
            name="amount_policy",
            status="warning",
            message="Amount is critical and requires senior approval.",
            evidence={"amount": amount, "critical_threshold": critical_threshold},
        )
    if amount >= approval_threshold:
        return CheckResult(
            name="amount_policy",
            status="warning",
            message="Amount exceeds approval threshold.",
            evidence={"amount": amount, "approval_threshold": approval_threshold},
        )
    return CheckResult(
        name="amount_policy",
        status="passed",
        message="Amount is within auto-allow threshold.",
        evidence={"amount": amount, "approval_threshold": approval_threshold},
    )


def check_evidence(req: PreflightRequest) -> CheckResult:
    if not req.invoice.evidence_urls:
        return CheckResult(
            name="evidence_attached",
            status="needs_evidence",
            message="No invoice evidence URL or document reference attached.",
            evidence={},
        )
    return CheckResult(
        name="evidence_attached",
        status="passed",
        message="Invoice evidence is attached.",
        evidence={"evidence_urls": req.invoice.evidence_urls},
    )


def check_intent_lock(conn, req: PreflightRequest, txn_id: str, policy: dict[str, Any]) -> CheckResult:
    cleanup_expired_locks(conn)
    key = invoice_lock_key(req)
    existing = conn.execute("SELECT * FROM intent_locks WHERE lock_key=?", (key,)).fetchone()
    if existing and existing["transaction_id"] != txn_id:
        return CheckResult(
            name="intent_lock",
            status="failed",
            message="Another agent transaction already holds this invoice intent lock.",
            evidence={"lock_key": key, "current_holder": existing["transaction_id"], "expires_at": existing["expires_at"]},
        )
    expires_at = lock_expires_at(policy)
    conn.execute(
        "INSERT OR REPLACE INTO intent_locks(lock_key, transaction_id, agent_id, expires_at, created_at) VALUES (?, ?, ?, ?, ?)",
        (key, txn_id, req.agent_id, expires_at.isoformat(), utc_now().isoformat()),
    )
    conn.commit()
    return CheckResult(
        name="intent_lock",
        status="passed",
        message="Intent lock granted for this invoice action.",
        evidence={"lock_key": key, "expires_at": expires_at.isoformat()},
    )


def decide(checks: list[CheckResult], req: PreflightRequest, policy: dict[str, Any]) -> tuple[str, str, str, list[str]]:
    failed = [c for c in checks if c.status == "failed"]
    missing = [c for c in checks if c.status == "needs_evidence"]
    warnings = [c for c in checks if c.status == "warning"]
    financial_actions = set(policy.get("financial_actions", ["pay_invoice", "post_journal_entry"]))
    if failed:
        return "blocked", "high", "send_to_human_review", ["execute_action"]
    if missing:
        return "needs_more_evidence", "medium", "attach_missing_evidence_and_rerun_preflight", ["execute_action"]
    if req.action in financial_actions:
        return "approval_required", "high", "request_finance_approval", ["execute_without_approval"]
    if warnings:
        return "approval_required", "medium", "request_finance_approval", ["execute_without_approval"]
    return "allow", "low", "execute_action", []


def run_preflight(conn, req: PreflightRequest) -> PreflightResponse:
    policy = get_policy(conn)
    allowed_actions = set(policy.get("allowed_actions", []))
    txn_id = transaction_id()
    expires_at = lock_expires_at(policy)

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

    checks.extend(
        [
            check_vendor(conn, req),
            check_duplicate(conn, req, policy),
            check_contract(conn, req, policy),
            check_amount_policy(req, policy),
            check_evidence(req),
            check_intent_lock(conn, req, txn_id, policy),
        ]
    )
    decision, risk, next_action, blocked_actions = decide(checks, req, policy)
    status = "blocked" if decision == "blocked" else "preflighted"

    # Store the invoice as seen so future duplicate checks can catch it.
    conn.execute(
        """
        INSERT OR REPLACE INTO invoices(
            invoice_id, vendor, amount, currency, invoice_date, due_date, gst_number,
            contract_id, evidence_json, line_items_json, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT status FROM invoices WHERE invoice_id=?), 'seen'), COALESCE((SELECT created_at FROM invoices WHERE invoice_id=?), ?))
        """,
        (
            req.invoice.invoice_id,
            req.invoice.vendor,
            req.invoice.amount,
            req.invoice.currency,
            req.invoice.invoice_date,
            req.invoice.due_date,
            req.invoice.gst_number,
            req.invoice.contract_id,
            dumps(req.invoice.evidence_urls),
            dumps(req.invoice.line_items),
            req.invoice.invoice_id,
            req.invoice.invoice_id,
            utc_now().isoformat(),
        ),
    )
    now = utc_now().isoformat()
    conn.execute(
        """
        INSERT INTO transactions(
            id, agent_id, user_id, intent, action, invoice_json, constraints_json,
            decision, risk, checks_json, allowed_next_action, blocked_actions_json,
            status, expires_at, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            txn_id,
            req.agent_id,
            req.user_id,
            req.intent,
            req.action,
            req.invoice.model_dump_json(),
            dumps(req.constraints),
            decision,
            risk,
            dumps([c.model_dump() for c in checks]),
            next_action,
            dumps(blocked_actions),
            status,
            expires_at.isoformat(),
            now,
            now,
        ),
    )
    conn.commit()
    return PreflightResponse(
        transaction_id=txn_id,
        decision=decision,  # type: ignore[arg-type]
        risk=risk,  # type: ignore[arg-type]
        checks=checks,
        allowed_next_action=next_action,
        blocked_actions=blocked_actions,
        expires_at=expires_at,
    )


def sign_receipt(payload: dict[str, Any]) -> str:
    body = dumps(payload).encode("utf-8")
    return hmac.new(RECEIPT_SECRET, body, hashlib.sha256).hexdigest()


def get_transaction(conn, txn_id: str):
    row = conn.execute("SELECT * FROM transactions WHERE id=?", (txn_id,)).fetchone()
    if not row:
        return None
    data = dict(row)
    for field in ["constraints_json", "checks_json", "blocked_actions_json", "approval_json", "execution_json", "receipt_json"]:
        data[field] = loads(data.get(field), None)
    data["invoice_json"] = loads(data["invoice_json"], {})
    return data

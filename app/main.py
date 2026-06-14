from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app import control
from app.auth import role_has_permission, verify_password
from app.models import ApprovalDecision, PreflightRequest, Receipt
from app.policy import get_transaction, receipt_id, run_preflight, sign_receipt
from app.approval_workflow import plan_approval_workflow, enforce_maker_checker
from app.api_security import require_api_scope
from fastapi import Depends
from app.store import (
    connect, dumps, get_accounting_writeback, get_uploaded_document, get_user_by_email,
    init_db, list_audit_events, list_audit_events_for_transaction, loads, save_accounting_writeback,
    save_uploaded_document, seed_demo, utc_now,
    create_approval_workflow, create_approval_step, get_approval_workflow_for_transaction,
    list_approval_steps_for_transaction, get_current_pending_approval_step,
    record_approval_step_decision, mark_workflow_approved_if_complete, mark_workflow_rejected
)

app = FastAPI(
    title="ActionRail Finance",
    description="Transaction runtime for finance AI agent actions: preflight, approval, execution, receipts.",
    version="0.1.0",
)

_SESSION_SECRET = os.environ.get("ACTIONRAIL_SESSION_SECRET")
if not _SESSION_SECRET:
    _SESSION_SECRET = "dev-only-actionrail-session-secret-change-me"

_APP_DIR = Path(__file__).resolve().parent
_REPO_DIR = _APP_DIR.parent
_UPLOAD_DIR = _REPO_DIR / "data" / "uploads"
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
_CONTRACT_EVIDENCE_DIR = _REPO_DIR / "data" / "contract_evidence"
_CONTRACT_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
_AUDIT_EXPORTS_DIR = _REPO_DIR / "data" / "audit_exports"
_AUDIT_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
_ACCOUNTING_PROVIDER = "local_accounting_sandbox"
app.add_middleware(SessionMiddleware, secret_key=_SESSION_SECRET, max_age=60 * 60 * 24 * 7)
app.mount("/static", StaticFiles(directory=_APP_DIR / "static"), name="static")
templates = Jinja2Templates(directory=_APP_DIR / "templates")
control.set_templates(templates)

conn = connect()
init_db(conn)
seed_demo(conn)


def _dash_ctx(request: Request, **extra: Any) -> dict[str, Any]:
    return control.page_context(request, conn, version=app.version, **extra)


def _dash_guard(request: Request, permission: str, target_type: str, target_id: str | None = None):
    user, redirect = control.require_login(request, conn)
    if redirect:
        return None, redirect
    denied = control.require_permission(
        request, conn, user=user, permission=permission,
        target_type=target_type, target_id=target_id, version=app.version,
    )
    if denied:
        return None, denied
    return user, None


def _dash_csrf(
    request: Request, user: dict[str, Any], csrf_token: str | None,
    target_type: str, target_id: str | None,
):
    return control.require_csrf(
        request, conn, user=user, csrf_token=csrf_token,
        target_type=target_type, target_id=target_id, version=app.version,
    )


# ---------------------------------------------------------------------------
# Health / manifest / preflight
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "service": "actionrail-finance"}


@app.get("/actionrail/manifest.json")
def manifest():
    return {
        "name": "ActionRail Finance",
        "version": "0.1.0",
        "description": "Agent-first transaction rail for finance actions.",
        "tools": [
            "preflight_action",
            "request_approval",
            "execute_transaction",
            "get_receipt",
            "list_transactions",
        ],
        "risk_levels": ["read_only", "draft", "internal_update", "external_action", "financial_transaction"],
    }


@app.post("/actions/preflight")
def preflight(req: PreflightRequest, request: Request, api_client: dict | None = Depends(require_api_scope("preflight:create"))):
    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key:
        from app.store import get_idempotency_record, save_idempotency_record, hash_request_body, utc_now
        from datetime import timedelta
        import json
        
        req_hash = hash_request_body(req.model_dump_json().encode())
        record = get_idempotency_record(conn, "preflight", idempotency_key)
        
        if record:
            if record["request_hash"] == req_hash:
                control.write_audit_event(
                    conn, request, action="idempotency_replayed", target_type="idempotency_key",
                    target_id=idempotency_key, event={"scope": "preflight"}
                )
                return json.loads(record["response_json"])
            else:
                control.write_audit_event(
                    conn, request, action="idempotency_conflict", target_type="idempotency_key",
                    target_id=idempotency_key, event={"scope": "preflight"}
                )
                raise HTTPException(status_code=409, detail="idempotency_conflict")

        resp = run_preflight(conn, req)
        
        expires_at = (utc_now() + timedelta(days=1)).isoformat()
        import uuid
        record_id = "idem_" + str(uuid.uuid4()).replace("-", "")
        save_idempotency_record(
            conn, record_id, "preflight", idempotency_key, req_hash,
            resp.model_dump_json(), 200, expires_at
        )
        control.write_audit_event(
            conn, request, action="idempotency_record_created", target_type="idempotency_key",
            target_id=idempotency_key, event={"scope": "preflight"}
        )
        return resp

    return run_preflight(conn, req)


@app.get("/transactions")
def list_transactions(limit: int = 25, api_client: dict | None = Depends(require_api_scope("transactions:read"))):
    rows = conn.execute(
        "SELECT id, agent_id, user_id, intent, action, decision, risk, status, created_at, updated_at "
        "FROM transactions ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return {"transactions": [dict(row) for row in rows]}


@app.get("/transactions/{transaction_id}")
def read_transaction(transaction_id: str, api_client: dict | None = Depends(require_api_scope("transactions:read"))):
    txn = get_transaction(conn, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="transaction_not_found")
    return txn


# ---------------------------------------------------------------------------
# Internal helpers — single source of truth for state-transition rules.
# Both the JSON API routes and the dashboard routes call these.
# Returning plain dicts keeps the JSON API response shape byte-identical.
# ---------------------------------------------------------------------------

def _create_workflow_if_needed(request: Request, transaction_id: str, user: dict[str, Any]):
    txn = get_transaction(conn, transaction_id)
    if not txn:
        return
    from app.store import get_policy
    policy = get_policy(conn)
    plan = plan_approval_workflow(txn, policy)
    if plan:
        create_approval_workflow(
            conn,
            workflow_id=plan["workflow_id"],
            transaction_id=transaction_id,
            workflow_type=plan["workflow_type"],
            status="pending",
            required_approvals=plan["required_approvals"],
            reason=plan["reason"]
        )
        for step in plan["steps"]:
            create_approval_step(
                conn,
                step_id=step["step_id"],
                workflow_id=plan["workflow_id"],
                transaction_id=transaction_id,
                step_order=step["step_order"],
                required_role=step["required_role"],
                status="pending"
            )
        control.write_audit_event(
            conn, request, action="approval_workflow_created", target_type="transaction",
            target_id=transaction_id,
            event={"workflow_id": plan["workflow_id"], "workflow_type": plan["workflow_type"]},
            actor=user
        )


def _approve_transaction(transaction_id: str, approver_id: str, note: str | None) -> dict[str, Any]:
    txn = get_transaction(conn, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="transaction_not_found")
    if txn["status"] == "blocked":
        raise HTTPException(status_code=400, detail="blocked_transaction_cannot_be_approved")
    if txn["status"] == "executed":
        raise HTTPException(status_code=400, detail="transaction_already_executed")
    approval = {
        "status": "approved",
        "approver_id": approver_id,
        "note": note,
        "approved_at": utc_now().isoformat(),
    }
    conn.execute(
        "UPDATE transactions SET status='approved', approval_json=?, updated_at=? WHERE id=?",
        (dumps(approval), utc_now().isoformat(), transaction_id),
    )
    conn.commit()
    return {"transaction_id": transaction_id, "status": "approved", "approval": approval}


def _reject_transaction(transaction_id: str, approver_id: str, note: str | None) -> dict[str, Any]:
    txn = get_transaction(conn, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="transaction_not_found")
    if txn["status"] == "executed":
        raise HTTPException(status_code=400, detail="transaction_already_executed")
    approval = {
        "status": "rejected",
        "approver_id": approver_id,
        "note": note,
        "rejected_at": utc_now().isoformat(),
    }
    conn.execute(
        "UPDATE transactions SET status='rejected', approval_json=?, updated_at=? WHERE id=?",
        (dumps(approval), utc_now().isoformat(), transaction_id),
    )
    conn.commit()
    return {"transaction_id": transaction_id, "status": "rejected", "approval": approval}


def _execute_transaction(transaction_id: str) -> dict[str, Any]:
    txn = get_transaction(conn, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="transaction_not_found")
    if txn["status"] == "blocked":
        raise HTTPException(status_code=400, detail="transaction_blocked")
    if txn["status"] == "rejected":
        raise HTTPException(status_code=400, detail="transaction_rejected")
    if txn["status"] == "executed":
        return {"transaction_id": transaction_id, "status": "already_executed", "receipt": txn["receipt_json"]}
    if txn["decision"] == "approval_required" and txn["status"] != "approved":
        raise HTTPException(status_code=400, detail="approval_required_before_execution")
    if txn["decision"] == "needs_more_evidence":
        raise HTTPException(status_code=400, detail="missing_evidence_blocks_execution")

    executed_at = utc_now()
    execution = {
        "status": "executed",
        "executed_at": executed_at.isoformat(),
        "note": "Demo execution only. No real bank or ledger mutation performed.",
    }
    receipt_payload = {
        "transaction_id": transaction_id,
        "action": txn["action"],
        "agent_id": txn["agent_id"],
        "user_id": txn["user_id"],
        "decision": txn["decision"],
        "invoice": txn["invoice_json"],
        "approval": txn["approval_json"],
        "execution": execution,
    }
    receipt = Receipt(
        receipt_id=receipt_id(),
        transaction_id=transaction_id,
        action=txn["action"],
        agent_id=txn["agent_id"],
        user_id=txn["user_id"],
        status="executed",
        executed_at=executed_at,
        receipt_signature=sign_receipt(receipt_payload),
        payload=receipt_payload,
    )
    conn.execute(
        "UPDATE transactions SET status='executed', execution_json=?, receipt_json=?, updated_at=? WHERE id=?",
        (dumps(execution), receipt.model_dump_json(), utc_now().isoformat(), transaction_id),
    )
    invoice_id = txn["invoice_json"].get("invoice_id")
    if invoice_id:
        conn.execute("UPDATE invoices SET status='approved' WHERE invoice_id=?", (invoice_id,))
    conn.commit()
    return {"transaction_id": transaction_id, "status": "executed", "receipt": receipt}


# ---------------------------------------------------------------------------
# JSON API routes (thin wrappers — preserve exact response shapes)
# ---------------------------------------------------------------------------

@app.post("/approvals/{transaction_id}/approve")
def approve_transaction(transaction_id: str, decision: ApprovalDecision):
    return _approve_transaction(transaction_id, decision.approver_id, decision.note)


@app.post("/approvals/{transaction_id}/reject")
def reject_transaction(transaction_id: str, decision: ApprovalDecision):
    return _reject_transaction(transaction_id, decision.approver_id, decision.note)


@app.post("/actions/{transaction_id}/execute")
def execute_transaction(transaction_id: str):
    return _execute_transaction(transaction_id)


@app.get("/receipts/{transaction_id}")
def get_receipt(transaction_id: str, api_client: dict | None = Depends(require_api_scope("receipts:read"))):
    txn = get_transaction(conn, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="transaction_not_found")
    if not txn["receipt_json"]:
        raise HTTPException(status_code=404, detail="receipt_not_found")
    return txn["receipt_json"]


# ---------------------------------------------------------------------------
# Dashboard helpers + view-model adapters
# ---------------------------------------------------------------------------

# Whitelist mapping. Any value not in this dict is rejected before touching disk
# so the URL cannot be used to read arbitrary files.
DEMO_EXAMPLES: dict[str, str] = {
    "approval_required": "invoice_approval_required.json",
    "duplicate_blocked": "invoice_duplicate_blocked.json",
    "missing_evidence": "invoice_missing_evidence.json",
}


def _load_demo_request(example_name: str) -> PreflightRequest:
    filename = DEMO_EXAMPLES.get(example_name)
    if not filename:
        raise HTTPException(status_code=404, detail="unknown_demo_example")
    path = _REPO_DIR / "examples" / filename
    payload = json.loads(path.read_text(encoding="utf-8"))
    return PreflightRequest.model_validate(payload)


def _row_to_listing(row) -> dict[str, Any]:
    """Project a transactions row plus its invoice JSON into the dashboard list view-model."""
    invoice = loads(row["invoice_json"], {}) or {}
    wf = get_approval_workflow_for_transaction(conn, row["id"])
    return {
        "id": row["id"],
        "agent_id": row["agent_id"],
        "intent": row["intent"],
        "action": row["action"],
        "vendor": invoice.get("vendor"),
        "amount": invoice.get("amount"),
        "currency": invoice.get("currency"),
        "decision": row["decision"],
        "risk": row["risk"],
        "status": row["status"],
        "created_at": row["created_at"],
        "workflow_status": wf["status"] if wf else None,
    }


def _detail_view_model(txn: dict[str, Any]) -> dict[str, Any]:
    """Shape a stored transaction for the detail template. Does not mutate state."""
    invoice = txn.get("invoice_json") or {}
    receipt_obj = txn.get("receipt_json")
    if isinstance(receipt_obj, str):
        try:
            receipt_obj = json.loads(receipt_obj)
        except json.JSONDecodeError:
            receipt_obj = None

    # Resolve uploaded document reference if present.
    uploaded_doc = None
    evidence_urls = invoice.get("evidence_urls") or []
    for url in evidence_urls:
        if isinstance(url, str) and url.startswith("local://uploaded_documents/"):
            doc_id = url.split("/")[-1]
            uploaded_doc = get_uploaded_document(conn, doc_id)
            break

    return {
        "id": txn["id"],
        "agent_id": txn["agent_id"],
        "user_id": txn["user_id"],
        "intent": txn["intent"],
        "action": txn["action"],
        "vendor": invoice.get("vendor"),
        "amount": invoice.get("amount"),
        "currency": invoice.get("currency"),
        "invoice_id": invoice.get("invoice_id"),
        "invoice": invoice,
        "decision": txn["decision"],
        "risk": txn["risk"],
        "status": txn["status"],
        "created_at": txn["created_at"],
        "updated_at": txn["updated_at"],
        "checks": txn.get("checks_json") or [],
        "allowed_next_action": txn["allowed_next_action"],
        "blocked_actions": txn.get("blocked_actions_json") or [],
        "approval": txn.get("approval_json"),
        "execution": txn.get("execution_json"),
        "receipt": receipt_obj,
        "uploaded_doc": uploaded_doc,
        "raw_json": json.dumps(txn, indent=2, default=str, ensure_ascii=False),
    }


def _can_approve(txn: dict[str, Any]) -> bool:
    return (
        txn["decision"] == "approval_required"
        and txn["status"] not in {"approved", "rejected", "executed", "blocked"}
    )


def _can_execute(txn: dict[str, Any]) -> bool:
    if txn["status"] in {"blocked", "rejected", "executed"}:
        return False
    if txn["decision"] == "blocked":
        return False
    if txn["decision"] == "needs_more_evidence":
        return False
    if txn["decision"] == "approval_required" and txn["status"] != "approved":
        return False
    return True


def _has_receipt(txn: dict[str, Any]) -> bool:
    return bool(txn.get("receipt") or txn.get("receipt_json"))


def _has_accounting_writeback(transaction_id: str) -> bool:
    return get_accounting_writeback(conn, transaction_id, _ACCOUNTING_PROVIDER) is not None


def _display_next_ui_action(txn: dict[str, Any], *, has_writeback: bool) -> str:
    """Human-correct next action for the dashboard UI. Does not mutate stored records."""
    status = txn.get("status", "")
    decision = txn.get("decision", "")

    if status == "executed":
        return (
            "view_accounting_sandbox_writeback"
            if has_writeback
            else "create_accounting_sandbox_writeback"
        )

    if decision == "blocked" or status == "blocked":
        return "send_to_human_review"

    if status == "rejected":
        return "none"

    if status == "approved":
        return "execute_action"

    if status == "preflighted" and decision == "approval_required":
        return "request_finance_approval"

    stored = txn.get("allowed_next_action")
    return stored if stored else "none"


def _transaction_state_summary(txn: dict[str, Any], *, has_writeback: bool) -> str | None:
    """Compact final-state note for screenshot-ready transaction detail."""
    status = txn.get("status", "")
    decision = txn.get("decision", "")

    if status == "executed":
        if has_writeback:
            return (
                "Execution complete. Signed receipt and local accounting sandbox "
                "writeback are available."
            )
        return (
            "Execution complete. A signed receipt exists. "
            "Accounting sandbox writeback is available."
        )

    if decision == "blocked" or status == "blocked":
        return "Transaction blocked by policy. Execution is unavailable."

    if decision == "approval_required" and status not in {"approved", "rejected", "executed"}:
        return "Finance approval is required before execution."

    return None


def _render_detail(
    request: Request,
    transaction_id: str,
    user: dict[str, Any],
    *,
    error: str | None = None,
    status_code: int = 200,
):
    txn = get_transaction(conn, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="transaction_not_found")
    vm = _detail_view_model(txn)
    has_wb = _has_accounting_writeback(transaction_id)
    role = user["role"]
    txn_audit = list_audit_events_for_transaction(conn, transaction_id, limit=30)
    wf = get_approval_workflow_for_transaction(conn, transaction_id)
    wf_steps = list_approval_steps_for_transaction(conn, transaction_id) if wf else []
    return templates.TemplateResponse(
        request,
        "transaction_detail.html",
        _dash_ctx(
            request,
            txn=vm,
            wf=wf,
            wf_steps=wf_steps,
            can_approve=_can_approve(txn) and role_has_permission(role, "approve_transaction"),
            can_execute=_can_execute(txn) and role_has_permission(role, "execute_transaction"),
            can_writeback=(
                txn["status"] == "executed"
                and role_has_permission(role, "accounting_writeback")
            ),
            has_receipt=_has_receipt(vm),
            has_accounting_writeback=has_wb,
            display_next_action=_display_next_ui_action(txn, has_writeback=has_wb),
            state_summary=_transaction_state_summary(txn, has_writeback=has_wb),
            transaction_audit_events=txn_audit,
            error=error,
        ),
        status_code=status_code,
    )


# ---------------------------------------------------------------------------
# Dashboard list view
# ---------------------------------------------------------------------------

_TERMINAL_QUEUE_STATUSES = frozenset({"executed", "approved", "rejected"})


def _compute_dashboard_stats(counts: list) -> dict[str, int]:
    """Count current operational queue state for dashboard stat cards only."""
    stats = {
        "total": 0,
        "approval_required": 0,
        "needs_evidence": 0,
        "blocked": 0,
        "executed": 0,
    }
    for row in counts:
        n = row["n"]
        decision = row["decision"]
        status = row["status"]
        stats["total"] += n

        if decision == "approval_required" and status == "preflighted":
            stats["approval_required"] += n

        if decision == "needs_more_evidence" and status not in _TERMINAL_QUEUE_STATUSES:
            stats["needs_evidence"] += n

        if status == "blocked" or decision == "blocked":
            stats["blocked"] += n

        if status == "executed":
            stats["executed"] += n

    return stats


# ---------------------------------------------------------------------------
# Login / logout / audit (control plane)
# ---------------------------------------------------------------------------

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request, error: str | None = None):
    user, redirect = control.require_login(request, conn)
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse(
        request,
        "login.html",
        _dash_ctx(request, error=error),
    )


@app.post("/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(default=""),
):
    csrf_resp = control.require_csrf(
        request, conn, user=None, csrf_token=csrf_token,
        target_type="login", target_id=None, version=app.version,
    )
    if csrf_resp:
        return templates.TemplateResponse(
            request,
            "login.html",
            _dash_ctx(request, error="Invalid or missing CSRF token."),
            status_code=400,
        )
    user = get_user_by_email(conn, email.strip().lower())
    if not user or not user.get("is_active"):
        control.write_audit_event(
            conn, request, action="login_failed", target_type="login",
            target_id=email, event={"reason": "unknown_or_inactive"},
        )
        return templates.TemplateResponse(
            request,
            "login.html",
            _dash_ctx(request, error="Invalid email or password."),
            status_code=401,
        )
    if not verify_password(password, user["password_salt"], user["password_hash"]):
        control.write_audit_event(
            conn, request, action="login_failed", target_type="login",
            target_id=email, event={"reason": "bad_password"},
        )
        return templates.TemplateResponse(
            request,
            "login.html",
            _dash_ctx(request, error="Invalid email or password."),
            status_code=401,
        )
    control.login_session(request, user)
    control.write_audit_event(
        conn, request, action="login_success", target_type="user",
        target_id=user["id"], actor=user,
    )
    return RedirectResponse(url="/dashboard", status_code=303)


@app.post("/logout")
def logout_submit(request: Request, csrf_token: str = Form(default="")):
    user = control.get_session_user(request, conn)
    csrf_resp = control.require_csrf(
        request, conn, user=user, csrf_token=csrf_token,
        target_type="logout", target_id=None, version=app.version,
    )
    if csrf_resp:
        return csrf_resp
    if user:
        control.write_audit_event(
            conn, request, action="logout", target_type="user",
            target_id=user["id"], actor=user,
        )
    control.logout_session(request)
    return RedirectResponse(url="/login", status_code=303)


@app.get("/dashboard/audit", response_class=HTMLResponse)
def dashboard_audit_log(request: Request):
    user, blocked = _dash_guard(request, "view_audit_log", "audit_log")
    if blocked:
        return blocked
    events = list_audit_events(conn, limit=100)
    return templates.TemplateResponse(
        request,
        "audit_log.html",
        _dash_ctx(request, events=events),
    )


from app.admin_routes import mount_admin_routes

import sys as _sys
_main_mod = _sys.modules[__name__]

mount_admin_routes(
    app,
    get_conn=lambda: _main_mod.conn,
    templates=templates,
    dash_ctx=_dash_ctx,
    dash_guard=_dash_guard,
    dash_csrf=_dash_csrf,
    version=app.version,
    get_evidence_dir=lambda: _CONTRACT_EVIDENCE_DIR,
)


# ---------------------------------------------------------------------------
# Dashboard list view
# ---------------------------------------------------------------------------

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user, blocked = _dash_guard(request, "view_dashboard", "dashboard")
    if blocked:
        return blocked
    rows = conn.execute(
        "SELECT id, agent_id, user_id, intent, action, invoice_json, decision, risk, status, created_at "
        "FROM transactions ORDER BY created_at DESC LIMIT 50"
    ).fetchall()
    counts = conn.execute(
        "SELECT decision, status, COUNT(*) AS n FROM transactions GROUP BY decision, status"
    ).fetchall()
    stats = _compute_dashboard_stats(counts)
    crowded = stats["total"] >= 10
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        _dash_ctx(
            request,
            rows=[_row_to_listing(row) for row in rows],
            stats=stats,
            crowded=crowded,
            demo_examples=list(DEMO_EXAMPLES.keys()),
            can_demo_preflight=role_has_permission(user["role"], "demo_preflight"),
        ),
    )


# ---------------------------------------------------------------------------
# Dashboard demo preflight
# ---------------------------------------------------------------------------

@app.post("/dashboard/demo/{example_name}")
def dashboard_demo_preflight(
    request: Request, example_name: str, csrf_token: str = Form(default=""),
):
    user, blocked = _dash_guard(request, "demo_preflight", "demo", example_name)
    if blocked:
        return blocked
    csrf_resp = _dash_csrf(request, user, csrf_token, "demo", example_name)
    if csrf_resp:
        return csrf_resp
    req = _load_demo_request(example_name)
    result = run_preflight(conn, req)
    control.write_audit_event(
        conn, request, action="demo_preflight_created", target_type="transaction",
        target_id=result.transaction_id,
        event={"example_name": example_name, "decision": result.decision},
        actor=user,
    )
    _create_workflow_if_needed(request, result.transaction_id, user)
    return RedirectResponse(
        url=f"/dashboard/transactions/{result.transaction_id}",
        status_code=303,
    )


# ---------------------------------------------------------------------------
# Dashboard transaction detail + actions + receipt
# ---------------------------------------------------------------------------

@app.get("/dashboard/transactions/{transaction_id}", response_class=HTMLResponse)
def dashboard_transaction_detail(request: Request, transaction_id: str, error: str | None = None):
    user, blocked = _dash_guard(request, "view_transaction", "transaction", transaction_id)
    if blocked:
        return blocked
    return _render_detail(request, transaction_id, user, error=error)


@app.post("/dashboard/transactions/{transaction_id}/approve")
def dashboard_approve(
    request: Request,
    transaction_id: str,
    note: str | None = Form(default=None),
    csrf_token: str = Form(default=""),
):
    user, blocked = _dash_guard(request, "approve_transaction", "transaction", transaction_id)
    if blocked:
        return blocked
    csrf_resp = _dash_csrf(request, user, csrf_token, "transaction", transaction_id)
    if csrf_resp:
        return csrf_resp
    try:
        txn = get_transaction(conn, transaction_id)
        if not txn:
            raise HTTPException(status_code=404, detail="transaction_not_found")

        wf = get_approval_workflow_for_transaction(conn, transaction_id)
        if not wf or wf["status"] != "pending":
            _approve_transaction(transaction_id, user["email"], note or None)
            control.write_audit_event(
                conn, request, action="transaction_approved", target_type="transaction",
                target_id=transaction_id, event={"note": note}, actor=user,
            )
        else:
            if not enforce_maker_checker(user, txn):
                control.write_audit_event(
                    conn, request, action="approval_separation_denied", target_type="transaction",
                    target_id=transaction_id, event={"reason": "maker cannot be checker"}, actor=user,
                )
                raise HTTPException(status_code=403, detail="Separation of duties: you cannot approve a transaction you created.")

            step = get_current_pending_approval_step(conn, transaction_id)
            if not step:
                raise HTTPException(status_code=400, detail="no_pending_steps")
            
            # Enforce role
            if user["role"] != step["required_role"] and user["role"] != "admin":
                control.write_audit_event(
                    conn, request, action="approval_wrong_role_denied", target_type="transaction",
                    target_id=transaction_id, event={"required_role": step["required_role"], "user_role": user["role"]}, actor=user,
                )
                raise HTTPException(status_code=403, detail=f"This step requires the {step['required_role']} role.")

            # Record step decision
            record_approval_step_decision(
                conn, step_id=step["id"], status="approved", 
                approver_user_id=user["id"], approver_email=user["email"], note=note
            )
            control.write_audit_event(
                conn, request, action="approval_step_completed", target_type="transaction",
                target_id=transaction_id, event={"step_id": step["id"], "note": note}, actor=user,
            )

            # Check if workflow is complete
            if mark_workflow_approved_if_complete(conn, transaction_id):
                _approve_transaction(transaction_id, user["email"], note or None)
                control.write_audit_event(
                    conn, request, action="transaction_approved", target_type="transaction",
                    target_id=transaction_id, event={"workflow_id": wf["id"]}, actor=user,
                )

    except HTTPException as exc:
        return _render_detail(
            request, transaction_id, user, error=str(exc.detail), status_code=exc.status_code,
        )
    return RedirectResponse(url=f"/dashboard/transactions/{transaction_id}", status_code=303)


@app.post("/dashboard/transactions/{transaction_id}/reject")
def dashboard_reject(
    request: Request,
    transaction_id: str,
    note: str | None = Form(default=None),
    csrf_token: str = Form(default=""),
):
    user, blocked = _dash_guard(request, "reject_transaction", "transaction", transaction_id)
    if blocked:
        return blocked
    csrf_resp = _dash_csrf(request, user, csrf_token, "transaction", transaction_id)
    if csrf_resp:
        return csrf_resp
    try:
        txn = get_transaction(conn, transaction_id)
        if not txn:
            raise HTTPException(status_code=404, detail="transaction_not_found")
            
        wf = get_approval_workflow_for_transaction(conn, transaction_id)
        if not wf or wf["status"] != "pending":
            _reject_transaction(transaction_id, user["email"], note or None)
            control.write_audit_event(
                conn, request, action="transaction_rejected", target_type="transaction",
                target_id=transaction_id, event={"note": note}, actor=user,
            )
        else:
            if not enforce_maker_checker(user, txn):
                control.write_audit_event(
                    conn, request, action="approval_separation_denied", target_type="transaction",
                    target_id=transaction_id, event={"reason": "maker cannot be checker"}, actor=user,
                )
                raise HTTPException(status_code=403, detail="Separation of duties: you cannot reject a transaction you created.")
                
            step = get_current_pending_approval_step(conn, transaction_id)
            if not step:
                raise HTTPException(status_code=400, detail="no_pending_steps")

            # Enforce role
            if user["role"] != step["required_role"] and user["role"] != "admin":
                control.write_audit_event(
                    conn, request, action="approval_wrong_role_denied", target_type="transaction",
                    target_id=transaction_id, event={"required_role": step["required_role"], "user_role": user["role"]}, actor=user,
                )
                raise HTTPException(status_code=403, detail=f"This step requires the {step['required_role']} role.")

            # Reject step and workflow
            record_approval_step_decision(
                conn, step_id=step["id"], status="rejected", 
                approver_user_id=user["id"], approver_email=user["email"], note=note
            )
            mark_workflow_rejected(conn, transaction_id)
            _reject_transaction(transaction_id, user["email"], note or None)

            control.write_audit_event(
                conn, request, action="approval_step_rejected", target_type="transaction",
                target_id=transaction_id, event={"step_id": step["id"], "note": note}, actor=user,
            )
            control.write_audit_event(
                conn, request, action="approval_workflow_rejected", target_type="transaction",
                target_id=transaction_id, event={"workflow_id": wf["id"]}, actor=user,
            )

    except HTTPException as exc:
        return _render_detail(
            request, transaction_id, user, error=str(exc.detail), status_code=exc.status_code,
        )
    return RedirectResponse(url=f"/dashboard/transactions/{transaction_id}", status_code=303)


@app.post("/dashboard/transactions/{transaction_id}/execute")
def dashboard_execute(
    request: Request,
    transaction_id: str,
    csrf_token: str = Form(default=""),
):
    user, blocked = _dash_guard(request, "execute_transaction", "transaction", transaction_id)
    if blocked:
        return blocked
    csrf_resp = _dash_csrf(request, user, csrf_token, "transaction", transaction_id)
    if csrf_resp:
        return csrf_resp
    try:
        wf = get_approval_workflow_for_transaction(conn, transaction_id)
        if wf and wf["status"] == "pending":
            control.write_audit_event(
                conn, request, action="execution_denied_workflow_pending", target_type="transaction",
                target_id=transaction_id, event={"workflow_id": wf["id"]}, actor=user,
            )
            raise HTTPException(status_code=400, detail="Cannot execute: approval workflow is still pending.")

        _execute_transaction(transaction_id)
        control.write_audit_event(
            conn, request, action="transaction_executed", target_type="transaction",
            target_id=transaction_id, actor=user,
        )
    except HTTPException as exc:
        return _render_detail(
            request, transaction_id, user, error=str(exc.detail), status_code=exc.status_code,
        )
    return RedirectResponse(url=f"/dashboard/transactions/{transaction_id}", status_code=303)


@app.get("/dashboard/transactions/{transaction_id}/receipt", response_class=HTMLResponse)
def dashboard_receipt(request: Request, transaction_id: str):
    user, blocked = _dash_guard(request, "view_receipt", "receipt", transaction_id)
    if blocked:
        return blocked
    txn = get_transaction(conn, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="transaction_not_found")
    vm = _detail_view_model(txn)
    control.write_audit_event(
        conn, request, action="receipt_viewed", target_type="receipt",
        target_id=transaction_id, actor=user,
    )
    return templates.TemplateResponse(
        request,
        "receipt.html",
        _dash_ctx(request, txn=vm),
    )


# ---------------------------------------------------------------------------
# Invoice upload — Phase 2D: two-step upload → review → submit
# ---------------------------------------------------------------------------

_ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
_ALLOWED_UPLOAD_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
}


def _doc_id() -> str:
    return f"doc_{uuid.uuid4().hex[:12]}"


def _sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --- Step 1: upload form ---------------------------------------------------

@app.get("/dashboard/invoices/upload", response_class=HTMLResponse)
def upload_invoice_form(request: Request):
    user, blocked = _dash_guard(request, "upload_invoice", "upload")
    if blocked:
        return blocked
    return templates.TemplateResponse(
        request,
        "invoice_upload.html",
        _dash_ctx(request, error=None),
    )


@app.post("/dashboard/invoices/upload")
async def upload_invoice_submit(
    request: Request,
    file: UploadFile = File(...),
    csrf_token: str = Form(default=""),
):
    user, blocked = _dash_guard(request, "upload_invoice", "upload")
    if blocked:
        return blocked
    csrf_resp = _dash_csrf(request, user, csrf_token, "upload", None)
    if csrf_resp:
        return csrf_resp
    """
    Validate the uploaded file, run extraction/OCR, save the uploaded_document
    record, then redirect to the review screen.  Does NOT create a transaction.
    """
    # --- Validate file type --------------------------------------------------
    suffix = Path(file.filename or "").suffix.lower()
    content_type = (file.content_type or "").split(";")[0].strip().lower()
    if suffix not in _ALLOWED_UPLOAD_EXTENSIONS or content_type not in _ALLOWED_UPLOAD_CONTENT_TYPES:
        return templates.TemplateResponse(
            request,
            "invoice_upload.html",
            _dash_ctx(
                request,
                error=(
                    f"Unsupported file type '{suffix}' / '{content_type}'. "
                    "Accepted: PDF, PNG, JPG."
                ),
            ),
            status_code=400,
        )

    # --- Read and hash -------------------------------------------------------
    file_bytes = await file.read()
    sha256 = _sha256_of_bytes(file_bytes)
    file_size = len(file_bytes)

    # --- Store file ----------------------------------------------------------
    doc_id = _doc_id()
    safe_name = f"{doc_id}{suffix}"
    dest = _UPLOAD_DIR / safe_name
    dest.write_bytes(file_bytes)

    # --- Extraction ----------------------------------------------------------
    from app.extraction import extract_fields_from_text, extract_text_from_pdf

    extracted_text: str | None = None
    extraction_result: dict = {"fields": {}, "notes": []}
    extraction_status = "not_attempted"
    ocr_metadata: dict = {}

    if suffix == ".pdf":
        extracted_text, extraction_status = extract_text_from_pdf(dest)
        if extracted_text:
            extraction_result = extract_fields_from_text(extracted_text)
    else:
        from app.ocr import ocr_image_bytes
        ocr_result = ocr_image_bytes(file_bytes, filename=file.filename)
        extraction_status = f"ocr:{ocr_result['status']}"
        ocr_metadata = {
            "status": ocr_result["status"],
            "engine": ocr_result["engine"],
            "notes": ocr_result.get("notes", []),
        }
        extraction_result["notes"].extend(
            [f"OCR engine: {ocr_result['engine']}", f"OCR status: {ocr_result['status']}"]
            + ocr_result.get("notes", [])
        )
        if ocr_result["status"] == "ok" and ocr_result.get("text"):
            extracted_text = ocr_result["text"]
            field_result = extract_fields_from_text(extracted_text)
            extraction_result["fields"].update(field_result.get("fields", {}))
            extraction_result["notes"].extend(field_result.get("notes", []))

    # --- Save document record ------------------------------------------------
    save_uploaded_document(
        conn,
        doc_id=doc_id,
        original_filename=file.filename or safe_name,
        stored_filename=safe_name,
        content_type=content_type,
        file_size=file_size,
        sha256=sha256,
        storage_path=str(dest),
        extracted_text=extracted_text,
        extracted_fields=extraction_result.get("fields", {}),
        extraction_notes=extraction_result.get("notes", []),
        extraction_status=extraction_status,
        ocr_metadata=ocr_metadata,
    )

    control.write_audit_event(
        conn, request, action="invoice_uploaded", target_type="uploaded_document",
        target_id=doc_id,
        event={"filename": file.filename, "sha256": sha256},
        actor=user,
    )

    return RedirectResponse(
        url=f"/dashboard/invoices/review/{doc_id}",
        status_code=303,
    )


# --- Step 2: review screen ------------------------------------------------

@app.get("/dashboard/invoices/review/{doc_id}", response_class=HTMLResponse)
def upload_invoice_review(request: Request, doc_id: str, error: str | None = None):
    user, blocked = _dash_guard(request, "review_invoice", "uploaded_document", doc_id)
    if blocked:
        return blocked
    doc = get_uploaded_document(conn, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="document_not_found")
    return templates.TemplateResponse(
        request,
        "invoice_review.html",
        _dash_ctx(request, doc=doc, error=error),
    )


# --- Step 3: submit review → create transaction ---------------------------

@app.post("/dashboard/invoices/review/{doc_id}/submit")
def upload_invoice_review_submit(
    request: Request,
    doc_id: str,
    invoice_id: str = Form(default=""),
    vendor: str = Form(default=""),
    amount: str = Form(default=""),
    currency: str = Form(default="INR"),
    invoice_date: str = Form(default=""),
    due_date: str = Form(default=""),
    gst_number: str = Form(default=""),
    contract_id: str = Form(default=""),
    line_items: str = Form(default=""),
    human_approval: str = Form(default=""),
    csrf_token: str = Form(default=""),
):
    user, blocked = _dash_guard(request, "review_invoice", "uploaded_document", doc_id)
    if blocked:
        return blocked
    csrf_resp = _dash_csrf(request, user, csrf_token, "uploaded_document", doc_id)
    if csrf_resp:
        return csrf_resp
    doc = get_uploaded_document(conn, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="document_not_found")

    # Collect confirmed fields (manual form always wins)
    confirmed: dict = {}
    if invoice_id.strip():
        confirmed["invoice_id"] = invoice_id.strip()
    if vendor.strip():
        confirmed["vendor"] = vendor.strip()
    if amount.strip():
        try:
            confirmed["amount"] = float(amount.strip().replace(",", ""))
        except ValueError:
            pass
    if currency.strip():
        confirmed["currency"] = currency.strip().upper()
    if invoice_date.strip():
        confirmed["invoice_date"] = invoice_date.strip()
    if due_date.strip():
        confirmed["due_date"] = due_date.strip()
    if gst_number.strip():
        confirmed["gst_number"] = gst_number.strip()
    if contract_id.strip():
        confirmed["contract_id"] = contract_id.strip()

    # Validate required fields
    missing = [f for f in ("invoice_id", "vendor", "amount") if not confirmed.get(f)]
    if missing:
        field_hints = {
            "amount":     "Amount is required. Enter it above.",
            "invoice_id": "Invoice ID is required. Enter it above.",
            "vendor":     "Vendor name is required. Enter it above.",
        }
        primary = field_hints.get(missing[0], f"{missing[0]} is required.")
        extra = f" Also missing: {', '.join(missing[1:])}." if len(missing) > 1 else ""
        # Re-render review page with the error
        doc_fresh = get_uploaded_document(conn, doc_id)
        return templates.TemplateResponse(
            request,
            "invoice_review.html",
            _dash_ctx(request, doc=doc_fresh, error=primary + extra),
            status_code=400,
        )

    # Build preflight request
    from app.models import InvoiceInput
    evidence_ref = f"local://uploaded_documents/{doc_id}"
    parsed_line_items = [
        ln.strip() for ln in (line_items or "").splitlines() if ln.strip()
    ]

    invoice_input = InvoiceInput(
        invoice_id=str(confirmed["invoice_id"]),
        vendor=str(confirmed["vendor"]),
        amount=float(confirmed["amount"]),
        currency=str(confirmed.get("currency", "INR")),
        invoice_date=confirmed.get("invoice_date") or None,
        due_date=confirmed.get("due_date") or None,
        gst_number=confirmed.get("gst_number") or None,
        contract_id=confirmed.get("contract_id") or None,
        evidence_urls=[evidence_ref],
        line_items=parsed_line_items or ["uploaded invoice"],
    )

    constraints: dict = {}
    if human_approval:
        constraints["human_approval_before_payment"] = True

    preflight_req = PreflightRequest(
        agent_id="dashboard_upload_user",
        user_id=user["email"],
        intent="pay_invoice",
        action="approve_invoice",
        invoice=invoice_input,
        constraints=constraints,
    )

    result = run_preflight(conn, preflight_req)
    control.write_audit_event(
        conn, request, action="invoice_review_submitted", target_type="transaction",
        target_id=result.transaction_id,
        event={"document_id": doc_id, "invoice_id": confirmed.get("invoice_id")},
        actor=user,
    )
    _create_workflow_if_needed(request, result.transaction_id, user)
    return RedirectResponse(
        url=f"/dashboard/transactions/{result.transaction_id}",
        status_code=303,
    )


# ---------------------------------------------------------------------------
# Accounting sandbox writeback — Phase 3A
# ---------------------------------------------------------------------------

@app.post("/dashboard/transactions/{transaction_id}/writeback/accounting-sandbox")
def dashboard_writeback_accounting_post(
    request: Request,
    transaction_id: str,
    csrf_token: str = Form(default=""),
):
    user, blocked = _dash_guard(request, "accounting_writeback", "accounting_writeback", transaction_id)
    if blocked:
        return blocked
    csrf_resp = _dash_csrf(request, user, csrf_token, "accounting_writeback", transaction_id)
    if csrf_resp:
        return csrf_resp
    txn = get_transaction(conn, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="transaction_not_found")

    if txn["status"] != "executed":
        return _render_detail(
            request, transaction_id, user,
            error="Accounting writeback requires an executed transaction. "
                  "Approve and execute the transaction first.",
            status_code=400,
        )

    existing = get_accounting_writeback(conn, transaction_id, _ACCOUNTING_PROVIDER)
    if existing:
        control.write_audit_event(
            conn, request, action="accounting_writeback_viewed", target_type="accounting_writeback",
            target_id=transaction_id, event={"idempotent": True}, actor=user,
        )
        return RedirectResponse(
            url=f"/dashboard/transactions/{transaction_id}/writeback/accounting-sandbox",
            status_code=303,
        )

    from app.accounting import LocalAccountingSandboxAdapter
    adapter = LocalAccountingSandboxAdapter()
    try:
        wb_result = adapter.create_draft_bill(txn)
    except ValueError as exc:
        return _render_detail(request, transaction_id, user, error=str(exc), status_code=400)

    save_accounting_writeback(
        conn,
        writeback_id=wb_result.writeback_id,
        transaction_id=transaction_id,
        provider=_ACCOUNTING_PROVIDER,
        status=wb_result.status,
        external_id=wb_result.external_id,
        result=wb_result.model_dump(),
    )
    control.write_audit_event(
        conn, request, action="accounting_writeback_created", target_type="accounting_writeback",
        target_id=transaction_id,
        event={"external_id": wb_result.external_id}, actor=user,
    )

    return RedirectResponse(
        url=f"/dashboard/transactions/{transaction_id}/writeback/accounting-sandbox",
        status_code=303,
    )


@app.get("/dashboard/transactions/{transaction_id}/writeback/accounting-sandbox", response_class=HTMLResponse)
def dashboard_writeback_accounting_get(request: Request, transaction_id: str):
    user, blocked = _dash_guard(request, "view_transaction", "accounting_writeback", transaction_id)
    if blocked:
        return blocked
    txn = get_transaction(conn, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="transaction_not_found")

    wb = get_accounting_writeback(conn, transaction_id, _ACCOUNTING_PROVIDER)
    if wb:
        control.write_audit_event(
            conn, request, action="accounting_writeback_viewed", target_type="accounting_writeback",
            target_id=transaction_id, actor=user,
        )

    draft_bill_data: dict | None = None
    audit_packet_data: dict | None = None
    if wb:
        from app.accounting import LocalAccountingSandboxAdapter

        adapter = LocalAccountingSandboxAdapter()
        db_path = adapter._draft_bills_dir / f"{transaction_id}.json"
        ap_path = adapter._audit_packets_dir / f"{transaction_id}.json"
        if db_path.exists():
            try:
                draft_bill_data = json.loads(db_path.read_text(encoding="utf-8"))
            except Exception:
                draft_bill_data = None
        if ap_path.exists():
            try:
                audit_packet_data = json.loads(ap_path.read_text(encoding="utf-8"))
            except Exception:
                audit_packet_data = None

    draft_bill_ref = f"local://accounting_sandbox/draft_bills/{transaction_id}"
    audit_packet_ref = f"local://accounting_sandbox/audit_packets/{transaction_id}"

    return templates.TemplateResponse(
        request,
        "accounting_writeback.html",
        _dash_ctx(
            request,
            txn=_detail_view_model(txn),
            wb=wb,
            draft_bill=draft_bill_data,
            audit_packet=audit_packet_data,
            draft_bill_ref=draft_bill_ref,
            audit_packet_ref=audit_packet_ref,
        ),
    )


# ---------------------------------------------------------------------------
# Phase 5E: Evidence Packs, Replay, Risk Monitor
# ---------------------------------------------------------------------------
from app.evidence_pack import build_transaction_evidence_pack
from app.replay import build_transaction_replay
from app.store import get_latest_evidence_export_for_transaction, save_evidence_export

@app.get("/dashboard/transactions/{transaction_id}/evidence-pack", response_class=HTMLResponse)
def dashboard_evidence_pack_get(request: Request, transaction_id: str):
    user, blocked = _dash_guard(request, "view_evidence_pack", "evidence_pack", transaction_id)
    if blocked:
        return blocked
    txn = get_transaction(conn, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="transaction_not_found")
        
    latest_export = get_latest_evidence_export_for_transaction(conn, transaction_id)
    pack = build_transaction_evidence_pack(conn, transaction_id, user)
    import json
    pack_json = json.dumps(pack, indent=2, default=str)
    
    control.write_audit_event(
        conn, request, action="evidence_pack_viewed", target_type="evidence_pack",
        target_id=transaction_id, actor=user,
    )
    return templates.TemplateResponse(
        request,
        "evidence_pack.html",
        _dash_ctx(
            request, 
            txn=_detail_view_model(txn), 
            pack=pack, 
            pack_json=pack_json,
            latest_export=latest_export,
            can_export=role_has_permission(user["role"], "export_evidence_pack")
        ),
    )

@app.post("/dashboard/transactions/{transaction_id}/evidence-pack/export")
def dashboard_evidence_pack_export(
    request: Request, transaction_id: str, csrf_token: str = Form(default="")
):
    user, blocked = _dash_guard(request, "export_evidence_pack", "evidence_pack", transaction_id)
    if blocked:
        return blocked
    csrf_resp = _dash_csrf(request, user, csrf_token, "evidence_pack", transaction_id)
    if csrf_resp:
        return csrf_resp
        
    txn = get_transaction(conn, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="transaction_not_found")
        
    pack = build_transaction_evidence_pack(conn, transaction_id, user)
    export_id = f"exp_{uuid.uuid4().hex[:12]}"
    filename = f"{transaction_id}_{export_id}.json"
    dest = _AUDIT_EXPORTS_DIR / filename
    
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(pack, f, indent=2, ensure_ascii=False)
        
    local_ref = f"local://audit_exports/{filename}"
    
    save_evidence_export(
        conn,
        export_id=export_id,
        transaction_id=transaction_id,
        actor_user_id=user["id"],
        actor_email=user["email"],
        pack_sha256=pack["evidence_pack_sha256"],
        local_ref=local_ref,
    )
    
    control.write_audit_event(
        conn, request, action="evidence_pack_exported", target_type="evidence_pack",
        target_id=transaction_id, event={"export_id": export_id, "local_ref": local_ref}, actor=user,
    )
    return RedirectResponse(url=f"/dashboard/transactions/{transaction_id}/evidence-pack", status_code=303)

@app.get("/dashboard/transactions/{transaction_id}/replay", response_class=HTMLResponse)
def dashboard_replay_get(request: Request, transaction_id: str):
    user, blocked = _dash_guard(request, "view_transaction_replay", "transaction_replay", transaction_id)
    if blocked:
        return blocked
    txn = get_transaction(conn, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="transaction_not_found")
        
    replay = build_transaction_replay(conn, transaction_id)
    policy_changed = "unchanged" not in replay.get("differences", [])
    replay_view = {
        "original_decision": replay["original_state"]["decision"],
        "replay_decision": replay["current_state"]["decision"],
        "differences": [d for d in replay.get("differences", []) if d != "unchanged"],
        "policy_changed": policy_changed
    }
    
    control.write_audit_event(
        conn, request, action="transaction_replayed", target_type="transaction",
        target_id=transaction_id, event={"differences": replay["differences"]}, actor=user,
    )
    return templates.TemplateResponse(
        request,
        "transaction_replay.html",
        _dash_ctx(request, txn=_detail_view_model(txn), replay=replay_view),
    )

@app.get("/dashboard/risk", response_class=HTMLResponse)
def dashboard_risk_monitor(request: Request):
    user, blocked = _dash_guard(request, "view_risk_monitor", "risk_monitor")
    if blocked:
        return blocked
        
    rows = conn.execute("SELECT decision, status, COUNT(*) AS n FROM transactions GROUP BY decision, status").fetchall()
    total_txns = 0
    blocked_txns = 0
    needs_evidence_txns = 0
    
    for row in rows:
        n = row["n"]
        total_txns += n
        if row["decision"] == "blocked" or row["status"] == "blocked":
            blocked_txns += n
        if row["decision"] == "needs_more_evidence":
            needs_evidence_txns += n
            
    recent_audit_events = list_audit_events(conn, limit=100)
    risk_events = [ev for ev in recent_audit_events if "denied" in ev["action"] or ev["action"] == "login_failed"]

    metrics = {
        "total_transactions": total_txns,
        "blocked_transactions": blocked_txns,
        "needs_evidence": needs_evidence_txns,
        "recent_security_events": len(risk_events)
    }

    control.write_audit_event(
        conn, request, action="risk_monitor_viewed", target_type="risk_monitor",
        target_id=None, actor=user,
    )
    return templates.TemplateResponse(
        request,
        "risk_monitor.html",
        _dash_ctx(request, metrics=metrics, risk_events=risk_events[:20]),
    )

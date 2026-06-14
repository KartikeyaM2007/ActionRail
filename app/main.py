from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.models import ApprovalDecision, PreflightRequest, Receipt
from app.policy import get_transaction, receipt_id, run_preflight, sign_receipt
from app.store import (
    connect, dumps, get_uploaded_document, get_accounting_writeback, init_db, loads,
    save_uploaded_document, save_accounting_writeback, seed_demo, utc_now,
)

app = FastAPI(
    title="ActionRail Finance",
    description="Transaction runtime for finance AI agent actions: preflight, approval, execution, receipts.",
    version="0.1.0",
)

_APP_DIR = Path(__file__).resolve().parent
_REPO_DIR = _APP_DIR.parent
_UPLOAD_DIR = _REPO_DIR / "data" / "uploads"
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
_ACCOUNTING_PROVIDER = "local_accounting_sandbox"
app.mount("/static", StaticFiles(directory=_APP_DIR / "static"), name="static")
templates = Jinja2Templates(directory=_APP_DIR / "templates")

conn = connect()
init_db(conn)
seed_demo(conn)


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
def preflight(req: PreflightRequest):
    return run_preflight(conn, req)


@app.get("/transactions")
def list_transactions(limit: int = 25):
    rows = conn.execute(
        "SELECT id, agent_id, user_id, intent, action, decision, risk, status, created_at, updated_at "
        "FROM transactions ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return {"transactions": [dict(row) for row in rows]}


@app.get("/transactions/{transaction_id}")
def read_transaction(transaction_id: str):
    txn = get_transaction(conn, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="transaction_not_found")
    return txn


# ---------------------------------------------------------------------------
# Internal helpers — single source of truth for state-transition rules.
# Both the JSON API routes and the dashboard routes call these.
# Returning plain dicts keeps the JSON API response shape byte-identical.
# ---------------------------------------------------------------------------

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
def get_receipt(transaction_id: str):
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

DASHBOARD_APPROVER_ID = "dashboard_user"


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


def _render_detail(request: Request, transaction_id: str, *, error: str | None = None, status_code: int = 200):
    txn = get_transaction(conn, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="transaction_not_found")
    vm = _detail_view_model(txn)
    has_wb = _has_accounting_writeback(transaction_id)
    return templates.TemplateResponse(
        request,
        "transaction_detail.html",
        {
            "txn": vm,
            "can_approve": _can_approve(txn),
            "can_execute": _can_execute(txn),
            "has_receipt": _has_receipt(vm),
            "has_accounting_writeback": has_wb,
            "display_next_action": _display_next_ui_action(txn, has_writeback=has_wb),
            "state_summary": _transaction_state_summary(txn, has_writeback=has_wb),
            "error": error,
            "static_url": "/static",
            "version": app.version,
        },
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


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
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
        {
            "rows": [_row_to_listing(row) for row in rows],
            "stats": stats,
            "crowded": crowded,
            "demo_examples": list(DEMO_EXAMPLES.keys()),
            "version": app.version,
            "static_url": "/static",
        },
    )


# ---------------------------------------------------------------------------
# Dashboard demo preflight
# ---------------------------------------------------------------------------

@app.post("/dashboard/demo/{example_name}")
def dashboard_demo_preflight(example_name: str):
    req = _load_demo_request(example_name)
    result = run_preflight(conn, req)
    return RedirectResponse(
        url=f"/dashboard/transactions/{result.transaction_id}",
        status_code=303,
    )


# ---------------------------------------------------------------------------
# Dashboard transaction detail + actions + receipt
# ---------------------------------------------------------------------------

@app.get("/dashboard/transactions/{transaction_id}", response_class=HTMLResponse)
def dashboard_transaction_detail(request: Request, transaction_id: str, error: str | None = None):
    return _render_detail(request, transaction_id, error=error)


@app.post("/dashboard/transactions/{transaction_id}/approve")
def dashboard_approve(request: Request, transaction_id: str, note: str | None = Form(default=None)):
    try:
        _approve_transaction(transaction_id, DASHBOARD_APPROVER_ID, note or None)
    except HTTPException as exc:
        return _render_detail(request, transaction_id, error=str(exc.detail), status_code=exc.status_code)
    return RedirectResponse(url=f"/dashboard/transactions/{transaction_id}", status_code=303)


@app.post("/dashboard/transactions/{transaction_id}/reject")
def dashboard_reject(request: Request, transaction_id: str, note: str | None = Form(default=None)):
    try:
        _reject_transaction(transaction_id, DASHBOARD_APPROVER_ID, note or None)
    except HTTPException as exc:
        return _render_detail(request, transaction_id, error=str(exc.detail), status_code=exc.status_code)
    return RedirectResponse(url=f"/dashboard/transactions/{transaction_id}", status_code=303)


@app.post("/dashboard/transactions/{transaction_id}/execute")
def dashboard_execute(request: Request, transaction_id: str):
    try:
        _execute_transaction(transaction_id)
    except HTTPException as exc:
        return _render_detail(request, transaction_id, error=str(exc.detail), status_code=exc.status_code)
    return RedirectResponse(url=f"/dashboard/transactions/{transaction_id}", status_code=303)


@app.get("/dashboard/transactions/{transaction_id}/receipt", response_class=HTMLResponse)
def dashboard_receipt(request: Request, transaction_id: str):
    txn = get_transaction(conn, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="transaction_not_found")
    vm = _detail_view_model(txn)
    return templates.TemplateResponse(
        request,
        "receipt.html",
        {
            "txn": vm,
            "static_url": "/static",
            "version": app.version,
        },
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
    return templates.TemplateResponse(
        request,
        "invoice_upload.html",
        {
            "static_url": "/static",
            "version": app.version,
            "error": None,
        },
    )


@app.post("/dashboard/invoices/upload")
async def upload_invoice_submit(
    request: Request,
    file: UploadFile = File(...),
):
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
            {
                "static_url": "/static",
                "version": app.version,
                "error": (
                    f"Unsupported file type '{suffix}' / '{content_type}'. "
                    "Accepted: PDF, PNG, JPG."
                ),
            },
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

    return RedirectResponse(
        url=f"/dashboard/invoices/review/{doc_id}",
        status_code=303,
    )


# --- Step 2: review screen ------------------------------------------------

@app.get("/dashboard/invoices/review/{doc_id}", response_class=HTMLResponse)
def upload_invoice_review(request: Request, doc_id: str, error: str | None = None):
    doc = get_uploaded_document(conn, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="document_not_found")
    return templates.TemplateResponse(
        request,
        "invoice_review.html",
        {
            "doc": doc,
            "error": error,
            "static_url": "/static",
            "version": app.version,
        },
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
):
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
            {
                "doc": doc_fresh,
                "error": primary + extra,
                "static_url": "/static",
                "version": app.version,
            },
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
        user_id="controller_001",
        intent="pay_invoice",
        action="approve_invoice",
        invoice=invoice_input,
        constraints=constraints,
    )

    result = run_preflight(conn, preflight_req)
    return RedirectResponse(
        url=f"/dashboard/transactions/{result.transaction_id}",
        status_code=303,
    )


# ---------------------------------------------------------------------------
# Accounting sandbox writeback — Phase 3A
# ---------------------------------------------------------------------------

@app.post("/dashboard/transactions/{transaction_id}/writeback/accounting-sandbox")
def dashboard_writeback_accounting_post(request: Request, transaction_id: str):
    txn = get_transaction(conn, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="transaction_not_found")

    if txn["status"] != "executed":
        return _render_detail(
            request, transaction_id,
            error="Accounting writeback requires an executed transaction. "
                  "Approve and execute the transaction first.",
            status_code=400,
        )

    # Idempotency: return existing writeback if already done
    existing = get_accounting_writeback(conn, transaction_id, _ACCOUNTING_PROVIDER)
    if existing:
        return RedirectResponse(
            url=f"/dashboard/transactions/{transaction_id}/writeback/accounting-sandbox",
            status_code=303,
        )

    from app.accounting import LocalAccountingSandboxAdapter
    adapter = LocalAccountingSandboxAdapter()
    try:
        wb_result = adapter.create_draft_bill(txn)
    except ValueError as exc:
        return _render_detail(
            request, transaction_id,
            error=str(exc),
            status_code=400,
        )

    save_accounting_writeback(
        conn,
        writeback_id=wb_result.writeback_id,
        transaction_id=transaction_id,
        provider=_ACCOUNTING_PROVIDER,
        status=wb_result.status,
        external_id=wb_result.external_id,
        result=wb_result.model_dump(),
    )

    return RedirectResponse(
        url=f"/dashboard/transactions/{transaction_id}/writeback/accounting-sandbox",
        status_code=303,
    )


@app.get("/dashboard/transactions/{transaction_id}/writeback/accounting-sandbox", response_class=HTMLResponse)
def dashboard_writeback_accounting_get(request: Request, transaction_id: str):
    txn = get_transaction(conn, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="transaction_not_found")

    wb = get_accounting_writeback(conn, transaction_id, _ACCOUNTING_PROVIDER)

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
        {
            "txn": _detail_view_model(txn),
            "wb": wb,
            "draft_bill": draft_bill_data,
            "audit_packet": audit_packet_data,
            "draft_bill_ref": draft_bill_ref,
            "audit_packet_ref": audit_packet_ref,
            "static_url": "/static",
            "version": app.version,
        },
    )

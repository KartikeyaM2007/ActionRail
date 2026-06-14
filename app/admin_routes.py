"""Dashboard admin routes: vendors, contracts, policy settings (Phase 5B)."""
from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Any, Callable

from fastapi import File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from app import control
from app.store import (
    create_contract,
    create_vendor,
    get_contract,
    get_policy,
    get_vendor,
    list_contract_evidence,
    list_contracts,
    list_vendors,
    save_contract_evidence,
    update_contract,
    update_policy_settings,
    update_vendor,
)

_ALLOWED_EVIDENCE_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
_ALLOWED_EVIDENCE_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
}


def mount_admin_routes(
    app,
    *,
    get_conn: Callable[[], Any],
    templates,
    dash_ctx: Callable[..., dict[str, Any]],
    dash_guard: Callable[..., tuple[Any, Any]],
    dash_csrf: Callable[..., Any],
    version: str,
    get_evidence_dir: Callable[[], Path],
) -> None:

    def _admin_guard(request: Request):
        return dash_guard(request, "manage_admin", "admin")

    @app.get("/dashboard/admin", response_class=HTMLResponse)
    def admin_index(request: Request):
        user, blocked = _admin_guard(request)
        if blocked:
            return blocked
        return templates.TemplateResponse(
            request,
            "admin_index.html",
            dash_ctx(
                request,
                vendor_count=len(list_vendors(get_conn())),
                contract_count=len(list_contracts(get_conn())),
            ),
        )

    @app.get("/dashboard/admin/vendors", response_class=HTMLResponse)
    def admin_vendors_list(request: Request, error: str | None = None, success: str | None = None):
        user, blocked = _admin_guard(request)
        if blocked:
            return blocked
        return templates.TemplateResponse(
            request,
            "admin_vendors.html",
            dash_ctx(request, vendors=list_vendors(get_conn()), error=error, success=success),
        )

    @app.post("/dashboard/admin/vendors")
    def admin_vendors_create(
        request: Request,
        name: str = Form(...),
        gst_number: str = Form(default=""),
        country: str = Form(default="IN"),
        status: str = Form(default="pending_review"),
        risk_level: str = Form(default="medium"),
        notes: str = Form(default=""),
        csrf_token: str = Form(default=""),
    ):
        user, blocked = _admin_guard(request)
        if blocked:
            return blocked
        csrf_resp = dash_csrf(request, user, csrf_token, "vendor", None)
        if csrf_resp:
            return csrf_resp
        vendor_id = f"vendor_{uuid.uuid4().hex[:10]}"
        try:
            create_vendor(
                get_conn(),
                vendor_id=vendor_id,
                name=name.strip(),
                gst_number=gst_number.strip() or None,
                country=country.strip() or "IN",
                status=status,
                risk_level=risk_level,
                notes=notes.strip() or None,
            )
            control.write_audit_event(
                get_conn(), request, action="vendor_created", target_type="vendor",
                target_id=vendor_id, event={"name": name.strip(), "status": status}, actor=user,
            )
        except Exception as exc:
            return templates.TemplateResponse(
                request,
                "admin_vendors.html",
                dash_ctx(request, vendors=list_vendors(get_conn()), error=str(exc)),
                status_code=400,
            )
        return RedirectResponse(url=f"/dashboard/admin/vendors/{vendor_id}", status_code=303)

    @app.get("/dashboard/admin/vendors/{vendor_id}", response_class=HTMLResponse)
    def admin_vendor_detail(request: Request, vendor_id: str, error: str | None = None, success: str | None = None):
        user, blocked = _admin_guard(request)
        if blocked:
            return blocked
        vendor = get_vendor(get_conn(), vendor_id)
        if not vendor:
            return templates.TemplateResponse(
                request, "forbidden.html",
                dash_ctx(request, error="Vendor not found."), status_code=404,
            )
        return templates.TemplateResponse(
            request,
            "admin_vendor_detail.html",
            dash_ctx(request, vendor=vendor, error=error, success=success),
        )

    @app.post("/dashboard/admin/vendors/{vendor_id}/update")
    def admin_vendor_update(
        request: Request,
        vendor_id: str,
        gst_number: str = Form(default=""),
        country: str = Form(default=""),
        status: str = Form(...),
        risk_level: str = Form(...),
        notes: str = Form(default=""),
        csrf_token: str = Form(default=""),
    ):
        user, blocked = _admin_guard(request)
        if blocked:
            return blocked
        csrf_resp = dash_csrf(request, user, csrf_token, "vendor", vendor_id)
        if csrf_resp:
            return csrf_resp
        old = get_vendor(get_conn(), vendor_id)
        if not old:
            return RedirectResponse(url="/dashboard/admin/vendors", status_code=303)
        update_vendor(
            get_conn(), vendor_id,
            gst_number=gst_number.strip() or None,
            country=country.strip() or old.get("country"),
            status=status,
            risk_level=risk_level,
            notes=notes.strip() or None,
        )
        action = "vendor_updated"
        if status == "blocked" and old.get("status") != "blocked":
            action = "vendor_blocked"
        elif status == "verified" and old.get("status") != "verified":
            action = "vendor_verified"
        control.write_audit_event(
            get_conn(), request, action=action, target_type="vendor",
            target_id=vendor_id, event={"status": status, "previous_status": old.get("status")}, actor=user,
        )
        return RedirectResponse(url=f"/dashboard/admin/vendors/{vendor_id}?success=1", status_code=303)

    @app.get("/dashboard/admin/contracts", response_class=HTMLResponse)
    def admin_contracts_list(request: Request, error: str | None = None):
        user, blocked = _admin_guard(request)
        if blocked:
            return blocked
        vendors = list_vendors(get_conn())
        return templates.TemplateResponse(
            request,
            "admin_contracts.html",
            dash_ctx(request, contracts=list_contracts(get_conn()), vendors=vendors, error=error),
        )

    @app.post("/dashboard/admin/contracts")
    def admin_contracts_create(
        request: Request,
        contract_id: str = Form(...),
        vendor_name: str = Form(...),
        max_amount: str = Form(...),
        currency: str = Form(default="INR"),
        start_date: str = Form(default=""),
        end_date: str = Form(default=""),
        status: str = Form(default="active"),
        terms: str = Form(default=""),
        notes: str = Form(default=""),
        csrf_token: str = Form(default=""),
    ):
        user, blocked = _admin_guard(request)
        if blocked:
            return blocked
        csrf_resp = dash_csrf(request, user, csrf_token, "contract", None)
        if csrf_resp:
            return csrf_resp
        cid = contract_id.strip()
        try:
            create_contract(
                get_conn(),
                contract_id=cid,
                vendor_name=vendor_name.strip(),
                max_amount=float(max_amount),
                currency=currency.strip() or "INR",
                start_date=start_date.strip() or None,
                end_date=end_date.strip() or None,
                status=status,
                evidence_url=None,
                terms=terms.strip() or None,
                notes=notes.strip() or None,
            )
            control.write_audit_event(
                get_conn(), request, action="contract_created", target_type="contract",
                target_id=cid, event={"vendor_name": vendor_name.strip(), "status": status}, actor=user,
            )
        except Exception as exc:
            return templates.TemplateResponse(
                request,
                "admin_contracts.html",
                dash_ctx(
                    request,
                    contracts=list_contracts(get_conn()),
                    vendors=list_vendors(get_conn()),
                    error=str(exc),
                ),
                status_code=400,
            )
        return RedirectResponse(url=f"/dashboard/admin/contracts/{cid}", status_code=303)

    @app.get("/dashboard/admin/contracts/{contract_id}", response_class=HTMLResponse)
    def admin_contract_detail(request: Request, contract_id: str, success: str | None = None):
        user, blocked = _admin_guard(request)
        if blocked:
            return blocked
        contract = get_contract(get_conn(), contract_id)
        if not contract:
            return templates.TemplateResponse(
                request, "forbidden.html",
                dash_ctx(request, error="Contract not found."), status_code=404,
            )
        evidence = list_contract_evidence(get_conn(), contract_id)
        return templates.TemplateResponse(
            request,
            "admin_contract_detail.html",
            dash_ctx(request, contract=contract, evidence_files=evidence, success=success),
        )

    @app.post("/dashboard/admin/contracts/{contract_id}/update")
    def admin_contract_update(
        request: Request,
        contract_id: str,
        max_amount: str = Form(...),
        currency: str = Form(default="INR"),
        start_date: str = Form(default=""),
        end_date: str = Form(default=""),
        status: str = Form(...),
        terms: str = Form(default=""),
        notes: str = Form(default=""),
        csrf_token: str = Form(default=""),
    ):
        user, blocked = _admin_guard(request)
        if blocked:
            return blocked
        csrf_resp = dash_csrf(request, user, csrf_token, "contract", contract_id)
        if csrf_resp:
            return csrf_resp
        old = get_contract(get_conn(), contract_id)
        if not old:
            return RedirectResponse(url="/dashboard/admin/contracts", status_code=303)
        update_contract(
            get_conn(), contract_id,
            max_amount=float(max_amount),
            currency=currency.strip() or "INR",
            start_date=start_date.strip() or None,
            end_date=end_date.strip() or None,
            status=status,
            terms=terms.strip() or None,
            notes=notes.strip() or None,
        )
        action = "contract_updated"
        if status == "active" and old.get("status") != "active":
            action = "contract_activated"
        elif status in {"inactive", "expired"} and old.get("status") == "active":
            action = "contract_deactivated"
        control.write_audit_event(
            get_conn(), request, action=action, target_type="contract",
            target_id=contract_id, event={"status": status, "previous_status": old.get("status")}, actor=user,
        )
        return RedirectResponse(url=f"/dashboard/admin/contracts/{contract_id}?success=1", status_code=303)

    @app.post("/dashboard/admin/contracts/{contract_id}/evidence")
    async def admin_contract_evidence_upload(
        request: Request,
        contract_id: str,
        file: UploadFile = File(...),
        csrf_token: str = Form(default=""),
    ):
        user, blocked = _admin_guard(request)
        if blocked:
            return blocked
        csrf_resp = dash_csrf(request, user, csrf_token, "contract_evidence", contract_id)
        if csrf_resp:
            return csrf_resp
        if not get_contract(get_conn(), contract_id):
            return RedirectResponse(url="/dashboard/admin/contracts", status_code=303)
        suffix = Path(file.filename or "").suffix.lower()
        content_type = file.content_type or ""
        if suffix not in _ALLOWED_EVIDENCE_EXTENSIONS or content_type not in _ALLOWED_EVIDENCE_TYPES:
            return RedirectResponse(
                url=f"/dashboard/admin/contracts/{contract_id}?error=unsupported_file",
                status_code=303,
            )
        file_bytes = await file.read()
        evidence_id = f"cev_{uuid.uuid4().hex[:12]}"
        sha256 = hashlib.sha256(file_bytes).hexdigest()
        safe_name = f"{evidence_id}{suffix}"
        evidence_dir = get_evidence_dir()
        evidence_dir.mkdir(parents=True, exist_ok=True)
        dest = evidence_dir / safe_name
        dest.write_bytes(file_bytes)
        save_contract_evidence(
            get_conn(),
            evidence_id=evidence_id,
            contract_id=contract_id,
            original_filename=file.filename or safe_name,
            stored_filename=safe_name,
            content_type=content_type,
            file_size=len(file_bytes),
            sha256=sha256,
            storage_path=str(dest),
        )
        control.write_audit_event(
            get_conn(), request, action="contract_evidence_uploaded", target_type="contract_evidence",
            target_id=evidence_id,
            event={"contract_id": contract_id, "sha256": sha256, "filename": file.filename},
            actor=user,
        )
        return RedirectResponse(url=f"/dashboard/admin/contracts/{contract_id}?success=evidence", status_code=303)

    @app.get("/dashboard/admin/policies", response_class=HTMLResponse)
    def admin_policies_view(request: Request, error: str | None = None, success: str | None = None):
        user, blocked = _admin_guard(request)
        if blocked:
            return blocked
        policy = get_policy(get_conn())
        return templates.TemplateResponse(
            request,
            "admin_policies.html",
            dash_ctx(request, policy=policy, error=error, success=success),
        )

    @app.post("/dashboard/admin/policies")
    def admin_policies_update(
        request: Request,
        approval_threshold: str = Form(...),
        require_contract_above: str = Form(...),
        duplicate_window_days: str = Form(...),
        lock_ttl_minutes: str = Form(...),
        csrf_token: str = Form(default=""),
    ):
        user, blocked = _admin_guard(request)
        if blocked:
            return blocked
        csrf_resp = dash_csrf(request, user, csrf_token, "policy", "finance_default")
        if csrf_resp:
            return csrf_resp
        old = get_policy(get_conn())
        new_policy = update_policy_settings(
            get_conn(),
            approval_threshold=float(approval_threshold),
            require_contract_above=float(require_contract_above),
            duplicate_window_days=int(duplicate_window_days),
            lock_ttl_minutes=int(lock_ttl_minutes),
        )
        control.write_audit_event(
            get_conn(), request, action="policy_updated", target_type="policy",
            target_id="finance_default",
            event={"previous": {k: old.get(k) for k in (
                "approval_threshold", "require_contract_above", "duplicate_window_days", "lock_ttl_minutes",
            )}, "new": {k: new_policy.get(k) for k in (
                "approval_threshold", "require_contract_above", "duplicate_window_days", "lock_ttl_minutes",
            )}},
            actor=user,
        )
        return RedirectResponse(url="/dashboard/admin/policies?success=1", status_code=303)

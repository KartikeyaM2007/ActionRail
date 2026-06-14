"""
Dashboard control plane: session user resolution, RBAC guards, audit logging.
"""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import ensure_csrf_token, role_has_permission, validate_csrf_token
from app.store import get_user_by_id, save_audit_event, utc_now

templates: Jinja2Templates | None = None  # set from main after templates init


def set_templates(t: Jinja2Templates) -> None:
    global templates
    templates = t


def get_session_user(request: Request, conn) -> dict[str, Any] | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = get_user_by_id(conn, user_id)
    if not user or not user.get("is_active"):
        return None
    return user


def login_session(request: Request, user: dict[str, Any]) -> None:
    request.session["user_id"] = user["id"]
    request.session["email"] = user["email"]
    request.session["role"] = user["role"]
    ensure_csrf_token(request.session)


def logout_session(request: Request) -> None:
    request.session.clear()


def page_context(request: Request, conn, *, version: str, **extra: Any) -> dict[str, Any]:
    user = get_session_user(request, conn)
    ctx: dict[str, Any] = {
        "current_user": user,
        "csrf_token": ensure_csrf_token(request.session),
        "can_view_audit": bool(user and role_has_permission(user["role"], "view_audit_log")),
        "static_url": "/static",
        "version": version,
    }
    ctx.update(extra)
    return ctx


def _request_id(request: Request) -> str:
    return request.headers.get("x-request-id") or request.headers.get("X-Request-ID") or ""


def write_audit_event(
    conn,
    request: Request,
    *,
    action: str,
    target_type: str,
    target_id: str | None = None,
    event: dict[str, Any] | None = None,
    actor: dict[str, Any] | None = None,
) -> None:
    user = actor or get_session_user(request, conn)
    save_audit_event(
        conn,
        event_id=f"aud_{uuid.uuid4().hex[:16]}",
        actor_user_id=user["id"] if user else None,
        actor_email=user["email"] if user else None,
        actor_role=user["role"] if user else None,
        action=action,
        target_type=target_type,
        target_id=target_id,
        request_id=_request_id(request) or None,
        event_json=event or {},
    )


def redirect_login() -> RedirectResponse:
    return RedirectResponse(url="/login", status_code=303)


def render_forbidden(request: Request, conn, *, version: str, message: str, status_code: int = 403):
    assert templates is not None
    return templates.TemplateResponse(
        request,
        "forbidden.html",
        page_context(request, conn, version=version, error=message),
        status_code=status_code,
    )


def require_login(request: Request, conn):
    """Return (user, None) or (None, RedirectResponse)."""
    user = get_session_user(request, conn)
    if not user:
        if request.session.get("user_id"):
            request.session.clear()
        return None, redirect_login()
    return user, None


def require_permission(
    request: Request,
    conn,
    *,
    user: dict[str, Any],
    permission: str,
    target_type: str,
    target_id: str | None,
    version: str,
):
    """Return None if allowed, else Forbidden Response."""
    if role_has_permission(user["role"], permission):
        return None
    write_audit_event(
        conn,
        request,
        action="authorization_denied",
        target_type=target_type,
        target_id=target_id,
        event={"permission": permission, "role": user["role"]},
        actor=user,
    )
    return render_forbidden(
        request,
        conn,
        version=version,
        message=f"Role '{user['role']}' is not allowed to perform this action ({permission}).",
    )


def require_csrf(
    request: Request,
    conn,
    *,
    user: dict[str, Any] | None,
    csrf_token: str | None,
    target_type: str,
    target_id: str | None,
    version: str,
):
    """Return None if valid, else Forbidden Response."""
    if validate_csrf_token(request.session, csrf_token):
        return None
    write_audit_event(
        conn,
        request,
        action="csrf_failed",
        target_type=target_type,
        target_id=target_id,
        event={"provided_token": bool(csrf_token)},
        actor=user,
    )
    return render_forbidden(
        request,
        conn,
        version=version,
        message="Invalid or missing CSRF token. Refresh the page and try again.",
        status_code=400,
    )

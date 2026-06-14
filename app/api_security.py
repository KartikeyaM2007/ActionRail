import hashlib
import hmac
import os
import secrets
from typing import Any, Callable

from fastapi import Depends, HTTPException, Request

from app.store import (
    connect,
    count_recent_api_requests,
    get_api_client_by_key_prefix,
    record_api_request_event,
    touch_api_client_last_used,
    loads,
)


def api_security_enabled() -> bool:
    return os.environ.get("ACTIONRAIL_REQUIRE_API_KEY", "0") == "1"


def extract_api_key(request: Request) -> str | None:
    return request.headers.get("X-ActionRail-API-Key")


def authenticate_api_client(conn, api_key: str) -> dict[str, Any] | None:
    parts = api_key.split("_")
    if len(parts) < 3:
        return None
    prefix = f"{parts[0]}_{parts[1]}"
    
    client = get_api_client_by_key_prefix(conn, prefix)
    if not client or not client["is_active"]:
        return None
    
    # Hash the provided key to compare with stored hash
    # "actionrail" was used as the salt in the demo seeder.
    provided_hash = hashlib.pbkdf2_hmac("sha256", api_key.encode(), b"actionrail", 100000).hex()
    
    if not hmac.compare_digest(provided_hash, client["client_key_hash"]):
        return None
        
    return client


def generate_api_key(prefix: str = "sk_local") -> tuple[str, str]:
    """Returns (raw_key, hashed_key)."""
    raw_secret = secrets.token_urlsafe(32)
    raw_key = f"{prefix}_{raw_secret}"
    hashed_key = hashlib.pbkdf2_hmac("sha256", raw_key.encode(), b"actionrail", 100000).hex()
    return raw_key, hashed_key


def require_api_scope(scope: str) -> Callable:
    def dependency(request: Request) -> dict[str, Any] | None:
        if not api_security_enabled():
            return None  # No identity when security is off
            
        api_key = extract_api_key(request)
        if not api_key:
            # We don't have access to conn here easily unless we open one or use request.state.conn
            # Let's open one for the auth layer or rely on app.main.conn if we have to.
            # Usually dependencies can yield a db connection. We'll just open a transient one for auth checks.
            _log_api_auth_failure(request, "missing_api_key")
            raise HTTPException(status_code=401, detail="missing_api_key")
            
        with connect() as conn:
            client = authenticate_api_client(conn, api_key)
            if not client:
                _log_api_auth_failure(request, "invalid_api_key")
                raise HTTPException(status_code=401, detail="invalid_api_key")
                
            allowed_scopes = loads(client["allowed_scopes_json"], [])
            if scope not in allowed_scopes:
                _log_api_scope_denied(request, client, scope)
                raise HTTPException(status_code=403, detail="scope_denied")
                
            # Rate limit check
            recent_requests = count_recent_api_requests(conn, client["id"], minutes=1)
            if recent_requests >= client["rate_limit_per_minute"]:
                _log_api_rate_limited(request, client)
                raise HTTPException(status_code=429, detail="rate_limit_exceeded")
                
            # Touch last used
            touch_api_client_last_used(conn, client["id"])
            
            # Record event
            event_id = "req_" + secrets.token_urlsafe(8)
            record_api_request_event(
                conn, event_id, client["id"], request.url.path, request.method, None
            )
            
            # Attach to request state
            request.state.api_client = client
            
            # Audit log success
            _log_api_client_authenticated(request, client, scope)
            
            return client
            
    return dependency


def _log_api_auth_failure(request: Request, reason: str):
    from app.control import write_audit_event
    with connect() as conn:
        write_audit_event(
            conn, request, action="api_auth_failed", target_type="api_request", target_id=request.url.path,
            event={"reason": reason, "route": request.url.path, "method": request.method}
        )


def _log_api_scope_denied(request: Request, client: dict[str, Any], scope: str):
    from app.control import write_audit_event
    with connect() as conn:
        write_audit_event(
            conn, request, action="api_scope_denied", target_type="api_client", target_id=client["id"],
            event={"client_name": client["name"], "scope_requested": scope, "route": request.url.path, "method": request.method}
        )


def _log_api_rate_limited(request: Request, client: dict[str, Any]):
    from app.control import write_audit_event
    with connect() as conn:
        write_audit_event(
            conn, request, action="api_rate_limited", target_type="api_client", target_id=client["id"],
            event={"client_name": client["name"], "route": request.url.path, "method": request.method, "limit": client["rate_limit_per_minute"]}
        )


def _log_api_client_authenticated(request: Request, client: dict[str, Any], scope: str):
    from app.control import write_audit_event
    with connect() as conn:
        write_audit_event(
            conn, request, action="api_client_authenticated", target_type="api_client", target_id=client["id"],
            event={"client_name": client["name"], "route": request.url.path, "method": request.method, "scope": scope}
        )

"""
Local dashboard authentication, RBAC, and CSRF helpers.

Demo-only credentials. Not production identity management.
Uses stdlib only: hashlib.pbkdf2_hmac, secrets, hmac.compare_digest.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Final

ROLES: Final[tuple[str, ...]] = (
    "admin",
    "controller",
    "approver",
    "executor",
    "auditor",
    "viewer",
)

# Permission → roles allowed (admin always allowed via role_has_permission).
ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "view_dashboard": frozenset({"viewer", "controller", "approver", "executor", "auditor", "admin"}),
    "view_transaction": frozenset({"viewer", "controller", "approver", "executor", "auditor", "admin"}),
    "view_receipt": frozenset({"viewer", "controller", "approver", "executor", "auditor", "admin"}),
    "upload_invoice": frozenset({"controller", "admin"}),
    "review_invoice": frozenset({"controller", "admin"}),
    "demo_preflight": frozenset({"controller", "admin"}),
    "approve_transaction": frozenset({"approver", "admin"}),
    "reject_transaction": frozenset({"approver", "admin"}),
    "execute_transaction": frozenset({"executor", "admin"}),
    "accounting_writeback": frozenset({"executor", "admin"}),
    "view_audit_log": frozenset({"auditor", "admin"}),
}

# Demo users: (id, email, display_name, role, password) — local demo only.
DEMO_USERS: tuple[tuple[str, str, str, str, str], ...] = (
    ("user_admin", "admin@example.local", "Admin User", "admin", "admin123"),
    ("user_controller", "controller@example.local", "Controller User", "controller", "controller123"),
    ("user_approver", "approver@example.local", "Approver User", "approver", "approver123"),
    ("user_executor", "executor@example.local", "Executor User", "executor", "executor123"),
    ("user_auditor", "auditor@example.local", "Auditor User", "auditor", "auditor123"),
    ("user_viewer", "viewer@example.local", "Viewer User", "viewer", "viewer123"),
)

_PBKDF2_ITERATIONS = 100_000


def hash_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    """Return (password_hash_hex, salt_hex)."""
    salt = salt_hex or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        _PBKDF2_ITERATIONS,
    )
    return digest.hex(), salt


def verify_password(password: str, salt_hex: str, password_hash_hex: str) -> bool:
    computed, _ = hash_password(password, salt_hex)
    return hmac.compare_digest(computed, password_hash_hex)


def role_has_permission(role: str, permission: str) -> bool:
    if role == "admin":
        return True
    allowed = ROLE_PERMISSIONS.get(permission)
    if not allowed:
        return False
    return role in allowed


def ensure_csrf_token(session: dict) -> str:
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_hex(32)
        session["csrf_token"] = token
    return token


def validate_csrf_token(session: dict, token: str | None) -> bool:
    expected = session.get("csrf_token")
    if not expected or not token:
        return False
    return hmac.compare_digest(str(expected), str(token))

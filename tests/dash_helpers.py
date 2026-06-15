"""Shared test helpers for dashboard auth, CSRF, and RBAC."""
from __future__ import annotations

import re

from fastapi.testclient import TestClient

DEMO_CREDENTIALS: dict[str, tuple[str, str]] = {
    "admin": ("admin@example.local", "admin123"),
    "controller": ("controller@example.local", "controller123"),
    "approver": ("approver@example.local", "approver123"),
    "executor": ("executor@example.local", "executor123"),
    "auditor": ("auditor@example.local", "auditor123"),
    "viewer": ("viewer@example.local", "viewer123"),
}


def extract_csrf(html: str) -> str:
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    assert m, "csrf_token hidden input not found in HTML"
    return m.group(1)


def login_as(client: TestClient, role: str = "admin") -> None:
    """Establish a session for the given demo role."""
    email, password = DEMO_CREDENTIALS[role]
    r = client.get("/login")
    if r.status_code == 303:
        body = client.get("/dashboard").text
        if f"Signed in as {email}" in body:
            return
        client.post("/logout", data={"csrf_token": extract_csrf(body)})
        r = client.get("/login")
    csrf = extract_csrf(r.text)
    r = client.post(
        "/login",
        data={"email": email, "password": password, "csrf_token": csrf},
    )
    assert r.status_code == 303, r.text


def csrf_from_session(client: TestClient, *, role: str = "admin") -> str:
    login_as(client, role)
    r = client.get("/dashboard")
    assert r.status_code == 200, r.text
    return extract_csrf(r.text)


def dash_get(client: TestClient, url: str, *, role: str = "viewer"):
    login_as(client, role)
    return client.get(url)


def dash_post(
    client: TestClient,
    url: str,
    *,
    role: str = "admin",
    data: dict | None = None,
    files: dict | None = None,
):
    login_as(client, role)
    payload = dict(data or {})
    payload.setdefault("csrf_token", csrf_from_session(client, role=role))
    if files is not None:
        return client.post(url, data=payload, files=files)
    return client.post(url, data=payload)

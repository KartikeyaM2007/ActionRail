from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import os
DB_PATH = Path(os.environ.get("ACTIONRAIL_DB_PATH", Path(__file__).resolve().parent.parent / "actionrail.db"))


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def connect(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def loads(value: Any, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    return json.loads(value)


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS vendors (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            verified INTEGER NOT NULL DEFAULT 0,
            gst_number TEXT,
            risk_level TEXT NOT NULL DEFAULT 'medium'
        );

        CREATE TABLE IF NOT EXISTS contracts (
            id TEXT PRIMARY KEY,
            vendor_name TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            max_amount REAL,
            terms TEXT,
            evidence_url TEXT
        );

        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id TEXT PRIMARY KEY,
            vendor TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL,
            invoice_date TEXT,
            due_date TEXT,
            gst_number TEXT,
            contract_id TEXT,
            evidence_json TEXT NOT NULL,
            line_items_json TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'seen',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS policies (
            key TEXT PRIMARY KEY,
            value_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS intent_locks (
            lock_key TEXT PRIMARY KEY,
            transaction_id TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            intent TEXT NOT NULL,
            action TEXT NOT NULL,
            invoice_json TEXT NOT NULL,
            constraints_json TEXT NOT NULL,
            decision TEXT NOT NULL,
            risk TEXT NOT NULL,
            checks_json TEXT NOT NULL,
            allowed_next_action TEXT NOT NULL,
            blocked_actions_json TEXT NOT NULL,
            status TEXT NOT NULL,
            approval_json TEXT,
            execution_json TEXT,
            receipt_json TEXT,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS uploaded_documents (
            id TEXT PRIMARY KEY,
            original_filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            content_type TEXT,
            file_size INTEGER,
            sha256 TEXT NOT NULL,
            storage_path TEXT NOT NULL,
            extracted_text TEXT,
            extracted_fields_json TEXT,
            extraction_notes_json TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS accounting_writebacks (
            id TEXT PRIMARY KEY,
            transaction_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            status TEXT NOT NULL,
            external_id TEXT,
            result_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(transaction_id, provider)
        );

        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_events (
            id TEXT PRIMARY KEY,
            actor_user_id TEXT,
            actor_email TEXT,
            actor_role TEXT,
            action TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_id TEXT,
            request_id TEXT,
            event_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS contract_evidence (
            id TEXT PRIMARY KEY,
            contract_id TEXT,
            original_filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            content_type TEXT,
            file_size INTEGER,
            sha256 TEXT NOT NULL,
            storage_path TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS approval_workflows (
            id TEXT PRIMARY KEY,
            transaction_id TEXT NOT NULL UNIQUE,
            workflow_type TEXT NOT NULL,
            status TEXT NOT NULL,
            required_approvals INTEGER NOT NULL,
            completed_approvals INTEGER NOT NULL DEFAULT 0,
            reason TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS approval_steps (
            id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            transaction_id TEXT NOT NULL,
            step_order INTEGER NOT NULL,
            required_role TEXT NOT NULL,
            status TEXT NOT NULL,
            approver_user_id TEXT,
            approver_email TEXT,
            note TEXT,
            created_at TEXT NOT NULL,
            decided_at TEXT
        );

        CREATE TABLE IF NOT EXISTS api_clients (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            client_key_hash TEXT NOT NULL,
            client_key_prefix TEXT NOT NULL,
            role TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            allowed_scopes_json TEXT NOT NULL,
            rate_limit_per_minute INTEGER NOT NULL DEFAULT 60,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_used_at TEXT
        );

        CREATE TABLE IF NOT EXISTS idempotency_records (
            id TEXT PRIMARY KEY,
            scope TEXT NOT NULL,
            idempotency_key TEXT NOT NULL,
            request_hash TEXT NOT NULL,
            response_json TEXT NOT NULL,
            status_code INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            UNIQUE(scope, idempotency_key)
        );

        CREATE TABLE IF NOT EXISTS api_request_events (
            id TEXT PRIMARY KEY,
            api_client_id TEXT,
            route TEXT NOT NULL,
            method TEXT NOT NULL,
            status_code INTEGER,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS evidence_exports (
            id TEXT PRIMARY KEY,
            transaction_id TEXT NOT NULL,
            actor_user_id TEXT,
            actor_email TEXT,
            pack_sha256 TEXT NOT NULL,
            local_ref TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    conn.commit()
    _migrate_schema(conn)


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1] for row in rows}


def _migrate_schema(conn: sqlite3.Connection) -> None:
    """Add Phase 5B columns without breaking existing demo DBs."""
    now = utc_now().isoformat()
    vcols = _table_columns(conn, "vendors")
    if "status" not in vcols:
        conn.execute("ALTER TABLE vendors ADD COLUMN status TEXT")
    if "country" not in vcols:
        conn.execute("ALTER TABLE vendors ADD COLUMN country TEXT")
    if "notes" not in vcols:
        conn.execute("ALTER TABLE vendors ADD COLUMN notes TEXT")
    if "created_at" not in vcols:
        conn.execute("ALTER TABLE vendors ADD COLUMN created_at TEXT")
    if "updated_at" not in vcols:
        conn.execute("ALTER TABLE vendors ADD COLUMN updated_at TEXT")
    conn.execute(
        """
        UPDATE vendors SET status='verified', country=COALESCE(country, 'IN'),
               created_at=COALESCE(created_at, ?), updated_at=COALESCE(updated_at, ?)
        WHERE verified=1 AND (status IS NULL OR status='')
        """,
        (now, now),
    )
    conn.execute(
        """
        UPDATE vendors SET status='pending_review', country=COALESCE(country, 'IN'),
               created_at=COALESCE(created_at, ?), updated_at=COALESCE(updated_at, ?)
        WHERE verified=0 AND (status IS NULL OR status='')
        """,
        (now, now),
    )

    ccols = _table_columns(conn, "contracts")
    if "status" not in ccols:
        conn.execute("ALTER TABLE contracts ADD COLUMN status TEXT")
    if "currency" not in ccols:
        conn.execute("ALTER TABLE contracts ADD COLUMN currency TEXT DEFAULT 'INR'")
    if "start_date" not in ccols:
        conn.execute("ALTER TABLE contracts ADD COLUMN start_date TEXT")
    if "end_date" not in ccols:
        conn.execute("ALTER TABLE contracts ADD COLUMN end_date TEXT")
    if "notes" not in ccols:
        conn.execute("ALTER TABLE contracts ADD COLUMN notes TEXT")
    if "created_at" not in ccols:
        conn.execute("ALTER TABLE contracts ADD COLUMN created_at TEXT")
    if "updated_at" not in ccols:
        conn.execute("ALTER TABLE contracts ADD COLUMN updated_at TEXT")
    conn.execute(
        """
        UPDATE contracts SET status='active', currency=COALESCE(currency, 'INR'),
               start_date=COALESCE(start_date, '2026-01-01'),
               end_date=COALESCE(end_date, '2027-12-31'),
               created_at=COALESCE(created_at, ?), updated_at=COALESCE(updated_at, ?)
        WHERE active=1 AND (status IS NULL OR status='')
        """,
        (now, now),
    )
    conn.execute(
        """
        UPDATE contracts SET status='inactive', currency=COALESCE(currency, 'INR'),
               created_at=COALESCE(created_at, ?), updated_at=COALESCE(updated_at, ?)
        WHERE active=0 AND (status IS NULL OR status='')
        """,
        (now, now),
    )
    conn.commit()


def seed_demo_users(conn: sqlite3.Connection) -> None:
    from app.auth import DEMO_USERS, hash_password

    for user_id, email, display_name, role, password in DEMO_USERS:
        pw_hash, salt = hash_password(password)
        conn.execute(
            """
            INSERT OR IGNORE INTO users(
                id, email, display_name, role, password_hash, password_salt, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (user_id, email, display_name, role, pw_hash, salt, utc_now().isoformat()),
        )
    conn.commit()


def seed_demo(conn: sqlite3.Connection) -> None:
    vendors = [
        ("vendor_acme", "Acme Services", 1, "27ABCDE1234F1Z5", "low"),
        ("vendor_aws", "AWS", 1, "29AAICA3918J1Z8", "low"),
        ("vendor_unknown", "Blue Moon Consulting", 0, None, "high"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO vendors(id, name, verified, gst_number, risk_level) VALUES (?, ?, ?, ?, ?)",
        vendors,
    )
    contracts = [
        ("ctr_acme_2026", "Acme Services", 1, 100000.0, "Monthly services up to ₹100,000", "https://evidence.local/contracts/acme-2026.pdf"),
        ("ctr_aws_2026", "AWS", 1, 250000.0, "Cloud usage budget", "https://evidence.local/contracts/aws-2026.pdf"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO contracts(id, vendor_name, active, max_amount, terms, evidence_url) VALUES (?, ?, ?, ?, ?, ?)",
        contracts,
    )
    default_policy = {
        "approval_threshold": 50000,
        "critical_threshold": 250000,
        "require_contract_above": 25000,
        "duplicate_window_days": 45,
        "lock_ttl_minutes": 15,
        "allowed_actions": [
            "approve_invoice",
            "pay_invoice",
            "post_journal_entry",
            "create_reconciliation_suggestion",
        ],
        "financial_actions": ["pay_invoice", "post_journal_entry"],
    }
    conn.execute(
        "INSERT OR IGNORE INTO policies(key, value_json) VALUES ('finance_default', ?)",
        (dumps(default_policy),),
    )
    # A paid historical invoice used for duplicate detection in the demo.
    conn.execute(
        """
        INSERT OR IGNORE INTO invoices(
            invoice_id, vendor, amount, currency, invoice_date, due_date, gst_number,
            contract_id, evidence_json, line_items_json, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "INV-1042",
            "Acme Services",
            82000.0,
            "INR",
            "2026-06-01",
            "2026-06-20",
            "27ABCDE1234F1Z5",
            "ctr_acme_2026",
            dumps(["https://evidence.local/invoices/INV-1042.pdf"]),
            dumps(["monthly development retainer"]),
            "paid",
            utc_now().isoformat(),
        ),
    )
    conn.commit()

    # Seed demo API client
    demo_client = conn.execute("SELECT id FROM api_clients WHERE id='client_demo'").fetchone()
    if not demo_client:
        import hashlib
        # Use a deterministic hash for the demo client so tests can predict it or we can just ignore secret.
        # "demo_secret_key"
        key_hash = hashlib.pbkdf2_hmac("sha256", b"demo_secret_key", b"actionrail", 100000).hex()
        conn.execute(
            """
            INSERT INTO api_clients (
                id, name, client_key_hash, client_key_prefix, role,
                allowed_scopes_json, rate_limit_per_minute, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "client_demo", "Local Demo Agent", key_hash, "sk_demo", "agent",
                dumps(["preflight:create", "transactions:read", "receipts:read"]),
                60, utc_now().isoformat(), utc_now().isoformat()
            )
        )
        conn.commit()

    seed_demo_users(conn)


def get_policy(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute("SELECT value_json FROM policies WHERE key='finance_default'").fetchone()
    if not row:
        return {}
    return loads(row["value_json"], {})


def save_policy(conn: sqlite3.Connection, policy: dict[str, Any]) -> None:
    conn.execute(
        "UPDATE policies SET value_json=? WHERE key='finance_default'",
        (dumps(policy),),
    )
    conn.commit()


def update_policy_settings(conn: sqlite3.Connection, **updates: Any) -> dict[str, Any]:
    policy = get_policy(conn)
    for key, value in updates.items():
        policy[key] = value
    save_policy(conn, policy)
    return policy


# ---------------------------------------------------------------------------
# Vendor admin helpers
# ---------------------------------------------------------------------------

def _vendor_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    if not data.get("status"):
        data["status"] = "verified" if data.get("verified") else "pending_review"
    data["verified"] = bool(data.get("verified", 0))
    return data


def list_vendors(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM vendors ORDER BY name").fetchall()
    return [_vendor_row_to_dict(row) for row in rows]


def get_vendor(conn: sqlite3.Connection, vendor_id: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM vendors WHERE id=?", (vendor_id,)).fetchone()
    if not row:
        return None
    return _vendor_row_to_dict(row)


def get_vendor_by_name(conn: sqlite3.Connection, name: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM vendors WHERE lower(name)=lower(?)", (name,)).fetchone()
    if not row:
        return None
    return _vendor_row_to_dict(row)


def create_vendor(
    conn: sqlite3.Connection,
    *,
    vendor_id: str,
    name: str,
    gst_number: str | None,
    country: str,
    status: str,
    risk_level: str,
    notes: str | None = None,
) -> dict[str, Any]:
    now = utc_now().isoformat()
    verified = 1 if status == "verified" else 0
    conn.execute(
        """
        INSERT INTO vendors(
            id, name, verified, gst_number, risk_level, country, status, notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (vendor_id, name, verified, gst_number, risk_level, country, status, notes, now, now),
    )
    conn.commit()
    return get_vendor(conn, vendor_id)  # type: ignore[return-value]


def update_vendor(
    conn: sqlite3.Connection,
    vendor_id: str,
    *,
    gst_number: str | None = None,
    country: str | None = None,
    status: str | None = None,
    risk_level: str | None = None,
    notes: str | None = None,
) -> dict[str, Any] | None:
    vendor = get_vendor(conn, vendor_id)
    if not vendor:
        return None
    now = utc_now().isoformat()
    new_status = status if status is not None else vendor["status"]
    verified = 1 if new_status == "verified" else 0
    conn.execute(
        """
        UPDATE vendors SET
            gst_number=?, country=?, status=?, risk_level=?, notes=?,
            verified=?, updated_at=?
        WHERE id=?
        """,
        (
            gst_number if gst_number is not None else vendor.get("gst_number"),
            country if country is not None else vendor.get("country"),
            new_status,
            risk_level if risk_level is not None else vendor.get("risk_level"),
            notes if notes is not None else vendor.get("notes"),
            verified,
            now,
            vendor_id,
        ),
    )
    conn.commit()
    return get_vendor(conn, vendor_id)


# ---------------------------------------------------------------------------
# Contract admin helpers
# ---------------------------------------------------------------------------

def _contract_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    if not data.get("status"):
        data["status"] = "active" if data.get("active") else "inactive"
    data["active"] = bool(data.get("active", 0))
    return data


def list_contracts(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM contracts ORDER BY vendor_name, id").fetchall()
    return [_contract_row_to_dict(row) for row in rows]


def get_contract(conn: sqlite3.Connection, contract_id: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM contracts WHERE id=?", (contract_id,)).fetchone()
    if not row:
        return None
    return _contract_row_to_dict(row)


def create_contract(
    conn: sqlite3.Connection,
    *,
    contract_id: str,
    vendor_name: str,
    max_amount: float,
    currency: str,
    start_date: str | None,
    end_date: str | None,
    status: str,
    evidence_url: str | None,
    terms: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    now = utc_now().isoformat()
    active = 1 if status == "active" else 0
    conn.execute(
        """
        INSERT INTO contracts(
            id, vendor_name, active, max_amount, terms, evidence_url,
            currency, start_date, end_date, status, notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            contract_id, vendor_name, active, max_amount, terms, evidence_url,
            currency, start_date, end_date, status, notes, now, now,
        ),
    )
    conn.commit()
    return get_contract(conn, contract_id)  # type: ignore[return-value]


def update_contract(
    conn: sqlite3.Connection,
    contract_id: str,
    *,
    max_amount: float | None = None,
    currency: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    status: str | None = None,
    evidence_url: str | None = None,
    terms: str | None = None,
    notes: str | None = None,
) -> dict[str, Any] | None:
    contract = get_contract(conn, contract_id)
    if not contract:
        return None
    now = utc_now().isoformat()
    new_status = status if status is not None else contract["status"]
    active = 1 if new_status == "active" else 0
    conn.execute(
        """
        UPDATE contracts SET
            max_amount=?, currency=?, start_date=?, end_date=?, status=?, active=?,
            evidence_url=?, terms=?, notes=?, updated_at=?
        WHERE id=?
        """,
        (
            max_amount if max_amount is not None else contract.get("max_amount"),
            currency if currency is not None else contract.get("currency"),
            start_date if start_date is not None else contract.get("start_date"),
            end_date if end_date is not None else contract.get("end_date"),
            new_status,
            active,
            evidence_url if evidence_url is not None else contract.get("evidence_url"),
            terms if terms is not None else contract.get("terms"),
            notes if notes is not None else contract.get("notes"),
            now,
            contract_id,
        ),
    )
    conn.commit()
    return get_contract(conn, contract_id)


def set_contract_status(conn: sqlite3.Connection, contract_id: str, status: str) -> dict[str, Any] | None:
    return update_contract(conn, contract_id, status=status)


# ---------------------------------------------------------------------------
# Contract evidence helpers
# ---------------------------------------------------------------------------

def save_contract_evidence(
    conn: sqlite3.Connection,
    *,
    evidence_id: str,
    contract_id: str,
    original_filename: str,
    stored_filename: str,
    content_type: str | None,
    file_size: int,
    sha256: str,
    storage_path: str,
) -> None:
    conn.execute(
        """
        INSERT INTO contract_evidence(
            id, contract_id, original_filename, stored_filename, content_type,
            file_size, sha256, storage_path, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            evidence_id, contract_id, original_filename, stored_filename, content_type,
            file_size, sha256, storage_path, utc_now().isoformat(),
        ),
    )
    ref = f"local://contract_evidence/{evidence_id}"
    update_contract(conn, contract_id, evidence_url=ref)


def list_contract_evidence(conn: sqlite3.Connection, contract_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM contract_evidence WHERE contract_id=? ORDER BY created_at DESC",
        (contract_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def create_user(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    email: str,
    display_name: str,
    role: str,
    password_hash: str,
    password_salt: str,
    is_active: bool = True,
) -> None:
    conn.execute(
        """
        INSERT INTO users(id, email, display_name, role, password_hash, password_salt, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            email,
            display_name,
            role,
            password_hash,
            password_salt,
            1 if is_active else 0,
            utc_now().isoformat(),
        ),
    )
    conn.commit()


def get_user_by_email(conn: sqlite3.Connection, email: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM users WHERE email=?", (email.lower(),)).fetchone()
    if not row:
        return None
    return _user_row_to_dict(row)


def get_user_by_id(conn: sqlite3.Connection, user_id: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not row:
        return None
    return _user_row_to_dict(row)


def list_users(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM users ORDER BY email").fetchall()
    return [_user_row_to_dict(row) for row in rows]


def _user_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["is_active"] = bool(data.get("is_active", 1))
    return data


def save_audit_event(
    conn: sqlite3.Connection,
    *,
    event_id: str,
    actor_user_id: str | None,
    actor_email: str | None,
    actor_role: str | None,
    action: str,
    target_type: str,
    target_id: str | None,
    request_id: str | None,
    event_json: dict[str, Any] | None,
) -> None:
    conn.execute(
        """
        INSERT INTO audit_events(
            id, actor_user_id, actor_email, actor_role, action, target_type,
            target_id, request_id, event_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            actor_user_id,
            actor_email,
            actor_role,
            action,
            target_type,
            target_id,
            request_id,
            dumps(event_json or {}),
            utc_now().isoformat(),
        ),
    )
    conn.commit()


def list_audit_events(conn: sqlite3.Connection, *, limit: int = 100) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM audit_events ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [_audit_row_to_dict(row) for row in rows]


def list_audit_events_for_transaction(conn: sqlite3.Connection, transaction_id: str, limit: int = 50) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM audit_events WHERE target_id=? ORDER BY created_at DESC LIMIT ?",
        (transaction_id, limit)
    ).fetchall()
    return [_audit_row_to_dict(r) for r in rows]


# ---------------------------------------------------------------------------
# API Client and Governance Helpers
# ---------------------------------------------------------------------------

def create_api_client(
    conn: sqlite3.Connection,
    client_id: str,
    name: str,
    client_key_hash: str,
    client_key_prefix: str,
    role: str,
    allowed_scopes: list[str],
    rate_limit_per_minute: int = 60
) -> None:
    now = utc_now().isoformat()
    conn.execute(
        """
        INSERT INTO api_clients (
            id, name, client_key_hash, client_key_prefix, role,
            allowed_scopes_json, rate_limit_per_minute, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            client_id, name, client_key_hash, client_key_prefix, role,
            dumps(allowed_scopes), rate_limit_per_minute, now, now
        )
    )
    conn.commit()


def get_api_client_by_key_prefix(conn: sqlite3.Connection, prefix: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM api_clients WHERE client_key_prefix = ?", (prefix,)).fetchone()
    if not row:
        return None
    return dict(row)


def get_api_client(conn: sqlite3.Connection, client_id: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM api_clients WHERE id = ?", (client_id,)).fetchone()
    if not row:
        return None
    return dict(row)


def list_api_clients(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM api_clients ORDER BY created_at DESC").fetchall()
    return [dict(row) for row in rows]


def update_api_client_status(conn: sqlite3.Connection, client_id: str, is_active: bool) -> None:
    conn.execute(
        "UPDATE api_clients SET is_active = ?, updated_at = ? WHERE id = ?",
        (1 if is_active else 0, utc_now().isoformat(), client_id)
    )
    conn.commit()


def touch_api_client_last_used(conn: sqlite3.Connection, client_id: str) -> None:
    conn.execute(
        "UPDATE api_clients SET last_used_at = ? WHERE id = ?",
        (utc_now().isoformat(), client_id)
    )
    conn.commit()


def hash_request_body(body: bytes) -> str:
    import hashlib
    return hashlib.sha256(body).hexdigest()


def save_idempotency_record(
    conn: sqlite3.Connection,
    record_id: str,
    scope: str,
    idempotency_key: str,
    request_hash: str,
    response_json: str,
    status_code: int,
    expires_at: str
) -> None:
    now = utc_now().isoformat()
    conn.execute(
        """
        INSERT INTO idempotency_records (
            id, scope, idempotency_key, request_hash, response_json, status_code, created_at, expires_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (record_id, scope, idempotency_key, request_hash, response_json, status_code, now, expires_at)
    )
    conn.commit()


def get_idempotency_record(conn: sqlite3.Connection, scope: str, idempotency_key: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM idempotency_records WHERE scope = ? AND idempotency_key = ?",
        (scope, idempotency_key)
    ).fetchone()
    if not row:
        return None
    return dict(row)


def cleanup_expired_idempotency_records(conn: sqlite3.Connection) -> None:
    now = utc_now().isoformat()
    conn.execute("DELETE FROM idempotency_records WHERE expires_at < ?", (now,))
    conn.commit()


def record_api_request_event(
    conn: sqlite3.Connection,
    event_id: str,
    api_client_id: str | None,
    route: str,
    method: str,
    status_code: int | None
) -> None:
    conn.execute(
        """
        INSERT INTO api_request_events (id, api_client_id, route, method, status_code, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (event_id, api_client_id, route, method, status_code, utc_now().isoformat())
    )
    conn.commit()


def count_recent_api_requests(conn: sqlite3.Connection, api_client_id: str, minutes: int = 1) -> int:
    cutoff = (utc_now() - timedelta(minutes=minutes)).isoformat()
    row = conn.execute(
        "SELECT COUNT(*) as count FROM api_request_events WHERE api_client_id = ? AND created_at >= ?",
        (api_client_id, cutoff)
    ).fetchone()
    return row["count"] if row else 0


def list_audit_events_for_transaction(
    conn: sqlite3.Connection, transaction_id: str, *, limit: int = 50
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT * FROM audit_events
        WHERE target_id=? OR instr(event_json, ?) > 0
        ORDER BY created_at DESC LIMIT ?
        """,
        (transaction_id, transaction_id, limit),
    ).fetchall()
    return [_audit_row_to_dict(row) for row in rows]


def _audit_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["event"] = loads(data.pop("event_json"), {})
    return data


def cleanup_expired_locks(conn: sqlite3.Connection) -> None:
    now = utc_now().isoformat()
    conn.execute("DELETE FROM intent_locks WHERE expires_at <= ?", (now,))
    conn.commit()


def lock_expires_at(policy: dict[str, Any]) -> datetime:
    ttl = int(policy.get("lock_ttl_minutes", 15))
    return utc_now() + timedelta(minutes=ttl)


def save_uploaded_document(
    conn: sqlite3.Connection,
    *,
    doc_id: str,
    original_filename: str,
    stored_filename: str,
    content_type: str | None,
    file_size: int,
    sha256: str,
    storage_path: str,
    extracted_text: str | None = None,
    extracted_fields: dict[str, Any] | None = None,
    extraction_notes: list[str] | None = None,
    extraction_status: str | None = None,
    ocr_metadata: dict[str, Any] | None = None,
) -> None:
    # Bundle OCR/extraction metadata into the fields JSON under a reserved key
    # so we don't need a schema migration.
    fields_payload: dict[str, Any] = dict(extracted_fields or {})
    fields_payload["_meta"] = {
        "extraction_status": extraction_status or "not_attempted",
        "ocr": ocr_metadata or {},
        "manual_review_required": not bool((extracted_fields or {}).get("amount")),
    }
    conn.execute(
        """
        INSERT INTO uploaded_documents(
            id, original_filename, stored_filename, content_type, file_size,
            sha256, storage_path, extracted_text, extracted_fields_json,
            extraction_notes_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            doc_id,
            original_filename,
            stored_filename,
            content_type,
            file_size,
            sha256,
            storage_path,
            extracted_text,
            dumps(fields_payload) if fields_payload is not None else None,
            dumps(extraction_notes or []),
            utc_now().isoformat(),
        ),
    )
    conn.commit()


def get_uploaded_document(conn: sqlite3.Connection, doc_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM uploaded_documents WHERE id=?", (doc_id,)
    ).fetchone()
    if not row:
        return None
    data = dict(row)
    raw_fields = loads(data.pop("extracted_fields_json"), {})
    # Separate internal metadata from user-facing extracted fields
    meta = raw_fields.pop("_meta", {})
    data["extracted_fields"] = raw_fields
    data["extraction_status"] = meta.get("extraction_status", "not_attempted")
    data["ocr_metadata"] = meta.get("ocr", {})
    data["manual_review_required"] = meta.get(
        "manual_review_required",
        not bool(raw_fields.get("amount")),
    )
    data["extraction_notes"] = loads(data.pop("extraction_notes_json"), [])
    return data


# ---------------------------------------------------------------------------
# Accounting writeback helpers
# ---------------------------------------------------------------------------

def save_accounting_writeback(
    conn: sqlite3.Connection,
    *,
    writeback_id: str,
    transaction_id: str,
    provider: str,
    status: str,
    external_id: str | None,
    result: Any,
) -> None:
    """
    Insert or replace an accounting writeback record.
    The UNIQUE(transaction_id, provider) constraint makes this idempotent:
    a second call for the same (transaction_id, provider) updates in place.
    """
    conn.execute(
        """
        INSERT INTO accounting_writebacks(id, transaction_id, provider, status, external_id, result_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(transaction_id, provider) DO UPDATE SET
            status=excluded.status,
            external_id=excluded.external_id,
            result_json=excluded.result_json
        """,
        (
            writeback_id,
            transaction_id,
            provider,
            status,
            external_id,
            dumps(result) if not isinstance(result, str) else result,
            utc_now().isoformat(),
        ),
    )
    conn.commit()


def get_accounting_writeback(
    conn: sqlite3.Connection, transaction_id: str, provider: str
) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM accounting_writebacks WHERE transaction_id=? AND provider=?",
        (transaction_id, provider),
    ).fetchone()
    if not row:
        return None
    data = dict(row)
    data["result"] = loads(data.pop("result_json"), {})
    return data


def list_accounting_writebacks(
    conn: sqlite3.Connection, *, limit: int = 50
) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM accounting_writebacks ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    result = []
    for row in rows:
        data = dict(row)
        data["result"] = loads(data.pop("result_json"), {})
        result.append(data)
    return result


# ---------------------------------------------------------------------------
# Approval Workflow helpers
# ---------------------------------------------------------------------------

def create_approval_workflow(
    conn: sqlite3.Connection,
    *,
    workflow_id: str,
    transaction_id: str,
    workflow_type: str,
    status: str,
    required_approvals: int,
    reason: str | None,
) -> None:
    now = utc_now().isoformat()
    conn.execute(
        """
        INSERT INTO approval_workflows(
            id, transaction_id, workflow_type, status, required_approvals,
            completed_approvals, reason, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
        """,
        (
            workflow_id, transaction_id, workflow_type, status, required_approvals,
            reason, now, now
        ),
    )
    conn.commit()


def create_approval_step(
    conn: sqlite3.Connection,
    *,
    step_id: str,
    workflow_id: str,
    transaction_id: str,
    step_order: int,
    required_role: str,
    status: str,
) -> None:
    now = utc_now().isoformat()
    conn.execute(
        """
        INSERT INTO approval_steps(
            id, workflow_id, transaction_id, step_order, required_role,
            status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (step_id, workflow_id, transaction_id, step_order, required_role, status, now),
    )
    conn.commit()


def get_approval_workflow_for_transaction(
    conn: sqlite3.Connection, transaction_id: str
) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM approval_workflows WHERE transaction_id=?", (transaction_id,)
    ).fetchone()
    return dict(row) if row else None


def list_approval_steps_for_transaction(
    conn: sqlite3.Connection, transaction_id: str
) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM approval_steps WHERE transaction_id=? ORDER BY step_order ASC",
        (transaction_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def get_current_pending_approval_step(
    conn: sqlite3.Connection, transaction_id: str
) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM approval_steps WHERE transaction_id=? AND status='pending' ORDER BY step_order ASC LIMIT 1",
        (transaction_id,),
    ).fetchone()
    return dict(row) if row else None


def record_approval_step_decision(
    conn: sqlite3.Connection,
    *,
    step_id: str,
    status: str,
    approver_user_id: str,
    approver_email: str,
    note: str | None,
) -> None:
    now = utc_now().isoformat()
    conn.execute(
        """
        UPDATE approval_steps SET
            status=?, approver_user_id=?, approver_email=?, note=?, decided_at=?
        WHERE id=?
        """,
        (status, approver_user_id, approver_email, note, now, step_id),
    )
    if status == 'approved':
        conn.execute(
            """
            UPDATE approval_workflows SET
                completed_approvals = completed_approvals + 1,
                updated_at = ?
            WHERE id = (SELECT workflow_id FROM approval_steps WHERE id=?)
            """,
            (now, step_id),
        )
    conn.commit()


def mark_workflow_approved_if_complete(
    conn: sqlite3.Connection, transaction_id: str
) -> bool:
    now = utc_now().isoformat()
    pending = conn.execute(
        "SELECT 1 FROM approval_steps WHERE transaction_id=? AND status='pending'",
        (transaction_id,)
    ).fetchone()
    
    if not pending:
        conn.execute(
            "UPDATE approval_workflows SET status='approved', updated_at=? WHERE transaction_id=?",
            (now, transaction_id)
        )
        conn.commit()
        return True
    return False


def mark_workflow_rejected(
    conn: sqlite3.Connection, transaction_id: str
) -> None:
    now = utc_now().isoformat()
    conn.execute(
        "UPDATE approval_workflows SET status='rejected', updated_at=? WHERE transaction_id=?",
        (now, transaction_id)
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Evidence Export Helpers
# ---------------------------------------------------------------------------

def save_evidence_export(
    conn: sqlite3.Connection,
    *,
    export_id: str,
    transaction_id: str,
    actor_user_id: str | None,
    actor_email: str | None,
    pack_sha256: str,
    local_ref: str,
) -> None:
    now = utc_now().isoformat()
    conn.execute(
        """
        INSERT INTO evidence_exports(
            id, transaction_id, actor_user_id, actor_email,
            pack_sha256, local_ref, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (export_id, transaction_id, actor_user_id, actor_email, pack_sha256, local_ref, now),
    )
    conn.commit()


def list_evidence_exports_for_transaction(
    conn: sqlite3.Connection, transaction_id: str
) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM evidence_exports WHERE transaction_id=? ORDER BY created_at DESC",
        (transaction_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def get_latest_evidence_export_for_transaction(
    conn: sqlite3.Connection, transaction_id: str
) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM evidence_exports WHERE transaction_id=? ORDER BY created_at DESC LIMIT 1",
        (transaction_id,),
    ).fetchone()
    return dict(row) if row else None

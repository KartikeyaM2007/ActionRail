from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent / "actionrail.db"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def connect(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def loads(value: str | None, default: Any = None) -> Any:
    if value is None:
        return default
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
        """
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


def get_policy(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute("SELECT value_json FROM policies WHERE key='finance_default'").fetchone()
    if not row:
        return {}
    return loads(row["value_json"], {})


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

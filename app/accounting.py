"""
ActionRail Finance — Accounting Sandbox Adapter.

This module provides a LOCAL sandbox adapter that:
- Creates draft bill JSON files after simulated execution
- Creates audit packet JSON files
- Never calls real ERP, bank, accounting API, or external services
- Returns a writeback result that ActionRail stores as proof

This is the foundation for later integration with real accounting adapters
(QuickBooks, Xero, Tally, Zoho, etc.), but this phase intentionally does NOT
connect to any external service.

Safety boundary (codified):
  Every result carries: "Local sandbox only. No ERP, bank, or ledger mutation performed."
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

# Repo root is parent of app/
_REPO_ROOT = Path(__file__).resolve().parent.parent
_DRAFT_BILLS_DIR = _REPO_ROOT / "data" / "accounting_sandbox" / "draft_bills"
_AUDIT_PACKETS_DIR = _REPO_ROOT / "data" / "accounting_sandbox" / "audit_packets"

SANDBOX_SAFETY_NOTE = "Local sandbox only. No ERP, bank, or ledger mutation performed."


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class AccountingDraftBill(BaseModel):
    """A draft bill created from an executed ActionRail transaction."""

    draft_bill_id: str
    transaction_id: str
    invoice_id: str | None = None
    vendor: str | None = None
    amount: float | None = None
    currency: str = "INR"
    invoice_date: str | None = None
    due_date: str | None = None
    line_items: list[str] = Field(default_factory=list)
    evidence_urls: list[str] = Field(default_factory=list)
    receipt_id: str | None = None
    receipt_signature: str | None = None
    source: str = "actionrail"
    provider: str = "local_accounting_sandbox"
    note: str = SANDBOX_SAFETY_NOTE
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AccountingAuditPacket(BaseModel):
    """A complete audit-ready packet for a transaction writeback."""

    audit_packet_id: str
    transaction_id: str
    transaction_json: dict[str, Any]
    receipt_json: dict[str, Any] | None = None
    checks_json: list[dict[str, Any]] = Field(default_factory=list)
    approval_json: dict[str, Any] | None = None
    execution_json: dict[str, Any] | None = None
    evidence_urls: list[str] = Field(default_factory=list)
    writeback_metadata: dict[str, Any] = Field(default_factory=dict)
    source: str = "actionrail"
    provider: str = "local_accounting_sandbox"
    note: str = SANDBOX_SAFETY_NOTE
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AccountingWritebackResult(BaseModel):
    """The outcome of an accounting writeback operation."""

    writeback_id: str
    transaction_id: str
    provider: str
    status: str  # "draft_created" | "already_exists" | "failed"
    external_id: str | None = None       # logical ID in the accounting system (sandbox: draft_bill_id)
    draft_bill_path: str | None = None   # relative path, never absolute
    audit_packet_path: str | None = None  # relative path, never absolute
    note: str = SANDBOX_SAFETY_NOTE
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# Local accounting sandbox adapter
# ---------------------------------------------------------------------------

class LocalAccountingSandboxAdapter:
    """
    A file-based sandbox adapter that creates draft bills and audit packets
    locally. Does not communicate with any external service.

    Intended as a foundation for future real adapters (QuickBooks, Xero, etc.).
    """

    provider: str = "local_accounting_sandbox"

    def __init__(self, draft_bills_dir: Path | None = None, audit_packets_dir: Path | None = None) -> None:
        self._draft_bills_dir = draft_bills_dir or _DRAFT_BILLS_DIR
        self._audit_packets_dir = audit_packets_dir or _AUDIT_PACKETS_DIR

    def _ensure_dirs(self) -> None:
        self._draft_bills_dir.mkdir(parents=True, exist_ok=True)
        self._audit_packets_dir.mkdir(parents=True, exist_ok=True)

    def create_draft_bill(self, transaction: dict[str, Any]) -> AccountingWritebackResult:
        """
        Create a draft bill JSON and audit packet JSON for an executed transaction.

        Args:
            transaction: A full transaction dict as returned by get_transaction().

        Returns:
            AccountingWritebackResult with status "draft_created".

        Raises:
            ValueError: If the transaction is not in "executed" status or has no receipt.
        """
        txn_id = transaction.get("id", "")

        # --- Guard: only execute transactions can be written back -----
        if transaction.get("status") != "executed":
            raise ValueError(
                f"Transaction {txn_id} has status '{transaction.get('status')}'; "
                "writeback requires status='executed'."
            )

        receipt_raw = transaction.get("receipt_json")
        if not receipt_raw:
            raise ValueError(
                f"Transaction {txn_id} has no receipt; cannot create accounting writeback."
            )

        import json
        # receipt_json may be stored as a JSON string or dict
        if isinstance(receipt_raw, str):
            try:
                receipt = json.loads(receipt_raw)
            except json.JSONDecodeError:
                receipt = {}
        else:
            receipt = receipt_raw or {}

        invoice = transaction.get("invoice_json") or {}
        checks = transaction.get("checks_json") or []
        approval = transaction.get("approval_json")
        execution = transaction.get("execution_json")

        self._ensure_dirs()

        # Stable IDs (deterministic so writeback is idempotent if regenerated)
        draft_bill_id = f"draft_{txn_id}"
        audit_packet_id = f"audit_{txn_id}"
        writeback_id = f"wb_{txn_id}"
        now = datetime.now(timezone.utc).isoformat()

        # --- Draft bill ---------------------------------------------------
        draft_bill = AccountingDraftBill(
            draft_bill_id=draft_bill_id,
            transaction_id=txn_id,
            invoice_id=invoice.get("invoice_id"),
            vendor=invoice.get("vendor"),
            amount=invoice.get("amount"),
            currency=invoice.get("currency", "INR"),
            invoice_date=invoice.get("invoice_date"),
            due_date=invoice.get("due_date"),
            line_items=invoice.get("line_items") or [],
            evidence_urls=invoice.get("evidence_urls") or [],
            receipt_id=receipt.get("receipt_id"),
            receipt_signature=receipt.get("receipt_signature"),
            created_at=now,
        )
        draft_path = self._draft_bills_dir / f"{txn_id}.json"
        draft_path.write_text(
            draft_bill.model_dump_json(indent=2), encoding="utf-8"
        )

        # --- Audit packet -------------------------------------------------
        audit_packet = AccountingAuditPacket(
            audit_packet_id=audit_packet_id,
            transaction_id=txn_id,
            transaction_json={k: v for k, v in transaction.items() if k != "receipt_json"},
            receipt_json=receipt,
            checks_json=checks if isinstance(checks, list) else [],
            approval_json=approval,
            execution_json=execution,
            evidence_urls=invoice.get("evidence_urls") or [],
            writeback_metadata={
                "writeback_id": writeback_id,
                "draft_bill_id": draft_bill_id,
                "provider": self.provider,
                "created_at": now,
            },
            created_at=now,
        )
        audit_path = self._audit_packets_dir / f"{txn_id}.json"
        audit_path.write_text(
            audit_packet.model_dump_json(indent=2), encoding="utf-8"
        )

        # Return relative paths so we never expose absolute local paths in the UI
        return AccountingWritebackResult(
            writeback_id=writeback_id,
            transaction_id=txn_id,
            provider=self.provider,
            status="draft_created",
            external_id=draft_bill_id,
            draft_bill_path=f"data/accounting_sandbox/draft_bills/{txn_id}.json",
            audit_packet_path=f"data/accounting_sandbox/audit_packets/{txn_id}.json",
            created_at=now,
        )

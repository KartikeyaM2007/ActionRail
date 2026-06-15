import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from app.policy import get_transaction
from app.store import (
    list_audit_events_for_transaction,
    get_uploaded_document,
    get_accounting_writeback,
    list_approval_steps_for_transaction,
    get_approval_workflow_for_transaction,
    get_contract,
    loads
)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def canonicalize_evidence_pack(pack: dict[str, Any]) -> str:
    """Canonicalize the evidence pack for hashing."""
    pack_copy = pack.copy()
    pack_copy.pop("evidence_pack_sha256", None)
    return json.dumps(pack_copy, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def hash_evidence_pack(pack: dict[str, Any]) -> str:
    """Hash the canonicalized evidence pack."""
    canonical = canonicalize_evidence_pack(pack)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def build_transaction_evidence_pack(conn, transaction_id: str, actor: dict[str, Any] | None = None) -> dict[str, Any]:
    txn = get_transaction(conn, transaction_id)
    if not txn:
        raise ValueError("Transaction not found")

    invoice = loads(txn.get("invoice_json"), {})

    # Audit events
    audit_events = list_audit_events_for_transaction(conn, transaction_id, limit=1000)

    # Workflow
    workflow = get_approval_workflow_for_transaction(conn, transaction_id)
    workflow_steps = list_approval_steps_for_transaction(conn, transaction_id) if workflow else []

    # Uploaded doc metadata (no raw bytes)
    uploaded_doc_meta = None
    evidence_urls = invoice.get("evidence_urls", [])
    for url in evidence_urls:
        if isinstance(url, str) and url.startswith("local://uploaded_documents/"):
            doc_id = url.split("/")[-1]
            doc = get_uploaded_document(conn, doc_id)
            if doc:
                uploaded_doc_meta = {
                    "id": doc["id"],
                    "original_filename": doc["original_filename"],
                    "content_type": doc.get("content_type"),
                    "file_size": doc.get("file_size"),
                    "sha256": doc["sha256"],
                    "extraction_status": doc.get("extraction_status"),
                    "ocr_metadata": loads(doc.get("ocr_metadata"), {}),
                    "created_at": doc["created_at"]
                }
            break

    # Contract metadata
    contract_meta = None
    contract_id = invoice.get("contract_id")
    if contract_id:
        contract = get_contract(conn, contract_id)
        if contract:
            contract_meta = {
                "id": contract["id"],
                "vendor_name": contract["vendor_name"],
                "status": contract["status"],
                "evidence_url": contract.get("evidence_url")
            }

    # Accounting sandbox writeback metadata
    # Module-level import to avoid circular dependency
    import app.main as _main
    wb = get_accounting_writeback(conn, transaction_id, _main._ACCOUNTING_PROVIDER)
    writeback_meta = None
    if wb:
        writeback_meta = {
            "id": wb["id"],
            "provider": wb["provider"],
            "status": wb["status"],
            "external_id": wb.get("external_id"),
            "created_at": wb["created_at"]
        }

    receipt_obj = txn.get("receipt_json")
    if isinstance(receipt_obj, str):
        try:
            receipt_obj = json.loads(receipt_obj)
        except json.JSONDecodeError:
            receipt_obj = None

    pack = {
        "pack_type": "actionrail_transaction_evidence_pack",
        "version": "1.0",
        "transaction_id": transaction_id,
        "generated_at": utc_now().isoformat(),
        "generated_by": actor["email"] if actor else "system",
        "safety_boundary": {
            "execution_simulated": True,
            "external_mutation_performed": False
        },
        "sections": {
            "transaction_record": {
                "id": txn["id"],
                "agent_id": txn["agent_id"],
                "user_id": txn["user_id"],
                "intent": txn["intent"],
                "action": txn["action"],
                "decision": txn["decision"],
                "risk": txn["risk"],
                "status": txn["status"],
                "allowed_next_action": txn["allowed_next_action"],
                "created_at": txn["created_at"],
                "updated_at": txn["updated_at"]
            },
            "invoice_payload": invoice,
            "policy_checks": loads(txn.get("checks_json"), []),
            "approval_workflow_summary": workflow,
            "approval_steps": workflow_steps,
            "transaction_audit_events": audit_events,
            "api_audit_events": [],  # Included for schema compatibility
            "uploaded_invoice_metadata": uploaded_doc_meta,
            "contract_metadata": contract_meta,
            "receipt_metadata": receipt_obj,
            "accounting_sandbox_writeback": writeback_meta
        }
    }

    pack["evidence_pack_sha256"] = hash_evidence_pack(pack)
    return pack

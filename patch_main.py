import sys

content = open('app/main.py', encoding='utf-8').read()

import_old = "from app.approval_workflow import plan_approval_workflow, enforce_maker_checker"
import_new = """from app.approval_workflow import plan_approval_workflow, enforce_maker_checker
from app.api_security import require_api_scope
from fastapi import Depends"""
if import_old in content and "require_api_scope" not in content:
    content = content.replace(import_old, import_new)


preflight_old = """@app.post("/actions/preflight")
def preflight(req: PreflightRequest):
    return run_preflight(conn, req)"""

preflight_new = """@app.post("/actions/preflight")
def preflight(req: PreflightRequest, request: Request, api_client: dict | None = Depends(require_api_scope("preflight:create"))):
    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key:
        from app.store import get_idempotency_record, save_idempotency_record, hash_request_body, utc_now
        from datetime import timedelta
        import json
        
        req_hash = hash_request_body(req.model_dump_json().encode())
        record = get_idempotency_record(conn, "preflight", idempotency_key)
        
        if record:
            if record["request_hash"] == req_hash:
                control.write_audit_event(
                    conn, request, action="idempotency_replayed", target_type="idempotency_key",
                    target_id=idempotency_key, event={"scope": "preflight"}
                )
                return json.loads(record["response_json"])
            else:
                control.write_audit_event(
                    conn, request, action="idempotency_conflict", target_type="idempotency_key",
                    target_id=idempotency_key, event={"scope": "preflight"}
                )
                raise HTTPException(status_code=409, detail="idempotency_conflict")

        resp = run_preflight(conn, req)
        
        expires_at = (utc_now() + timedelta(days=1)).isoformat()
        import uuid
        record_id = "idem_" + str(uuid.uuid4()).replace("-", "")
        save_idempotency_record(
            conn, record_id, "preflight", idempotency_key, req_hash,
            json.dumps(resp), 200, expires_at
        )
        control.write_audit_event(
            conn, request, action="idempotency_record_created", target_type="idempotency_key",
            target_id=idempotency_key, event={"scope": "preflight"}
        )
        return resp

    return run_preflight(conn, req)"""

if preflight_old in content:
    content = content.replace(preflight_old, preflight_new)

list_old = """@app.get("/transactions")
def list_transactions(limit: int = 25):"""

list_new = """@app.get("/transactions")
def list_transactions(limit: int = 25, api_client: dict | None = Depends(require_api_scope("transactions:read"))):"""

if list_old in content:
    content = content.replace(list_old, list_new)

get_old = """@app.get("/transactions/{transaction_id}")
def read_transaction(transaction_id: str):"""

get_new = """@app.get("/transactions/{transaction_id}")
def read_transaction(transaction_id: str, api_client: dict | None = Depends(require_api_scope("transactions:read"))):"""

if get_old in content:
    content = content.replace(get_old, get_new)

receipt_old = """@app.get("/receipts/{transaction_id}")
def get_receipt(transaction_id: str):"""

receipt_new = """@app.get("/receipts/{transaction_id}")
def get_receipt(transaction_id: str, api_client: dict | None = Depends(require_api_scope("receipts:read"))):"""

if receipt_old in content:
    content = content.replace(receipt_old, receipt_new)


open('app/main.py', 'w', encoding='utf-8').write(content)
print('Updated main.py successfully')

# Route Map

## Public / auth routes
- `GET /health` (purpose: healthcheck, CSRF: no, JSON: yes)
- `GET /actionrail/manifest.json` (purpose: agent discovery, CSRF: no, JSON: yes)
- `GET /login` (purpose: login form, CSRF: no, JSON: no)
- `POST /login` (purpose: auth submission, CSRF: yes, JSON: no)
- `POST /logout` (purpose: end session, CSRF: yes, JSON: no)

## Dashboard routes
- `GET /dashboard` (purpose: list transactions, role: view_dashboard, CSRF: no, JSON: no)
- `POST /dashboard/demo/{example_name}` (purpose: trigger demo, role: demo_preflight, CSRF: yes, JSON: no)

## Invoice upload/review routes
- `GET /dashboard/invoices/upload` (purpose: upload form, role: upload_invoice, CSRF: no, JSON: no)
- `POST /dashboard/invoices/upload` (purpose: process upload, role: upload_invoice, CSRF: no, JSON: no)
- `GET /dashboard/invoices/review/{doc_id}` (purpose: review extracted data, role: upload_invoice, CSRF: no, JSON: no)
- `POST /dashboard/invoices/review/{doc_id}/submit` (purpose: submit to preflight, role: upload_invoice, CSRF: yes, JSON: no)

## Transaction action routes
- `GET /dashboard/transactions/{transaction_id}` (purpose: detail view, role: view_transaction, CSRF: no, JSON: no)
- `POST /dashboard/transactions/{transaction_id}/approve` (purpose: approve, role: approve_transaction, CSRF: yes, JSON: no)
- `POST /dashboard/transactions/{transaction_id}/reject` (purpose: reject, role: reject_transaction, CSRF: yes, JSON: no)
- `POST /dashboard/transactions/{transaction_id}/execute` (purpose: execute, role: execute_transaction, CSRF: yes, JSON: no)
- `GET /dashboard/transactions/{transaction_id}/evidence_pack` (purpose: download evidence zip, role: view_evidence_pack, CSRF: no, JSON: no)
- `GET /dashboard/transactions/{transaction_id}/replay` (purpose: view policy replay, role: view_transaction_replay, CSRF: no, JSON: no)

## Receipt routes
- `GET /dashboard/transactions/{transaction_id}/receipt` (purpose: view signed receipt, role: view_receipt, CSRF: no, JSON: no)

## Accounting sandbox writeback routes
- `GET /dashboard/transactions/{transaction_id}/writeback/accounting-sandbox` (purpose: view writeback form, role: accounting_writeback, CSRF: no, JSON: no)
- `POST /dashboard/transactions/{transaction_id}/writeback/accounting-sandbox` (purpose: process writeback, role: accounting_writeback, CSRF: yes, JSON: no)

## Audit & Risk routes
- `GET /dashboard/audit` (purpose: view ledger, role: view_audit_log, CSRF: no, JSON: no)
- `GET /dashboard/risk` (purpose: view risk metrics, role: view_risk_monitor, CSRF: no, JSON: no)

## Admin routes
- `GET /dashboard/admin` (purpose: admin index, role: manage_admin, CSRF: no, JSON: no)
- `GET /dashboard/admin/vendors` (purpose: list vendors, role: manage_admin, CSRF: no, JSON: no)
- `POST /dashboard/admin/vendors` (purpose: create vendor, role: manage_admin, CSRF: yes, JSON: no)
- `GET /dashboard/admin/vendors/{vendor_id}` (purpose: view vendor, role: manage_admin, CSRF: no, JSON: no)
- `POST /dashboard/admin/vendors/{vendor_id}/update` (purpose: update vendor, role: manage_admin, CSRF: yes, JSON: no)
- `GET /dashboard/admin/contracts` (purpose: list contracts, role: manage_admin, CSRF: no, JSON: no)
- `POST /dashboard/admin/contracts` (purpose: create contract, role: manage_admin, CSRF: yes, JSON: no)
- `GET /dashboard/admin/contracts/{contract_id}` (purpose: view contract, role: manage_admin, CSRF: no, JSON: no)
- `POST /dashboard/admin/contracts/{contract_id}/update` (purpose: update contract, role: manage_admin, CSRF: yes, JSON: no)
- `POST /dashboard/admin/contracts/{contract_id}/evidence` (purpose: upload evidence, role: manage_admin, CSRF: yes, JSON: no)
- `GET /dashboard/admin/policies` (purpose: view policies, role: manage_admin, CSRF: no, JSON: no)
- `POST /dashboard/admin/policies` (purpose: update policies, role: manage_admin, CSRF: yes, JSON: no)

## JSON API routes
- `POST /actions/preflight` (purpose: preflight action, CSRF: no, JSON: yes)
- `GET /transactions` (purpose: list API txns, CSRF: no, JSON: yes)
- `GET /transactions/{transaction_id}` (purpose: get txn, CSRF: no, JSON: yes)
- `POST /approvals/{transaction_id}/approve` (purpose: API approve, CSRF: no, JSON: yes)
- `POST /approvals/{transaction_id}/reject` (purpose: API reject, CSRF: no, JSON: yes)
- `POST /actions/{transaction_id}/execute` (purpose: API execute, CSRF: no, JSON: yes)
- `GET /receipts/{transaction_id}` (purpose: API receipt, CSRF: no, JSON: yes)

# Schema Map

Current SQLite tables in `app/store.py`:

- `users`: Stores local auth users with roles, hashed passwords, and salts.
- `audit_events`: Append-only ledger of state mutations (auth, admin, approvals).
- `vendors`: Registered vendor records with risk_level, gst_number, verification status.
- `contracts`: Registered contracts tied to vendors, with limits, terms, active status.
- `policies`: Key-value JSON store for global configuration (e.g., `finance_default` thresholds).
- `uploaded_documents`: Stores metadata for user file uploads, extraction results, and storage paths.
- `transactions`: Core proposed actions, holding intents, invoices, constraints, decisions, risk, and JSON receipts.
- `intent_locks`: Idempotency keys mapping unique intents to transactions to prevent duplication.
- `accounting_writebacks`: Stores the result of local sandbox ledger integration (draft bills).
- `contract_evidence`: Uploaded files serving as contract proof, referencing `contracts`.
- `invoices`: Extracted/simulated invoice records, referenced by transactions for history and deduplication.

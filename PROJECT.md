# ActionRail Finance Project Knowledge Base

## 0. Purpose of this file

This file is the single source of truth for building **ActionRail Finance** in Cursor. Keep it in the project root as `PROJECT.md`. When Cursor or any AI coding agent works on this repo, it should read this file before changing code.

This project began as **ActionRail**, a transaction runtime for AI agent actions. The first production wedge is **finance operations**, because finance has high-value actions where mistakes are expensive, workflows are evidence-based, and approvals/audit trails are mandatory.

---

## 1. Final project identity

### Name

**ActionRail Finance**

### One-line pitch

**ActionRail Finance is a transaction runtime for finance AI agents. Before an agent approves, pays, posts, reconciles, or submits a finance action, ActionRail checks evidence, applies policy, routes approval, executes safely, and creates an audit-ready receipt.**

### Short YC-style pitch

AI agents are starting to perform finance work, but finance actions cannot be raw tool calls. A wrong payment, duplicate invoice, bad journal entry, or unsupported reconciliation creates real business damage. ActionRail turns every risky finance agent action into a transaction: verify evidence, enforce policy, lock duplicates, route approval, execute safely, and generate an audit-ready receipt. We start with invoice approval and duplicate detection, then expand into payments, journals, reconciliations, vendor onboarding, and close workflows.

### Long-term vision

ActionRail becomes the standard execution layer under vertical AI agents. Finance is the first wedge. Later, the same transaction primitive can support travel booking, commerce checkout, HR actions, legal approvals, DevOps changes, and any high-risk agent action.

---

## 2. Core thesis

### The wrong model

Most agent products treat actions like simple tool calls:

```text
agent -> call tool -> action happens
```

That is dangerous for finance.

### The ActionRail model

Every meaningful agent action becomes an explicit transaction:

```text
agent -> create transaction -> preflight -> verify -> lock -> approve -> execute -> receipt
```

### Why finance first

Finance workflows are a strong first wedge because they are:

1. Evidence-based: invoices, contracts, purchase orders, bank statements, ledger entries.
2. Policy-driven: amount thresholds, vendor approval, GL rules, approval chains.
3. High-risk: wrong payments, duplicate invoices, bad journals, audit failures.
4. Measurable: reduced manual review, faster close, fewer exceptions, better audit trail.
5. Willingness-to-pay positive: finance teams pay for control, compliance, and reduced labor.

### Important strategic framing

Do **not** pitch this as a generic finance chatbot.

Do **not** pitch this as full ERP replacement in v1.

Pitch it as:

```text
The safe execution rail between AI finance agents and systems of record.
```

---

## 3. Current MVP state

The MVP already has a FastAPI backend and basic dashboard.

### Current visible API routes

The Swagger/OpenAPI page currently shows these endpoints:

```text
GET  /health
GET  /actionrail/manifest.json
POST /actions/preflight
GET  /transactions
GET  /transactions/{transaction_id}
POST /approvals/{transaction_id}/approve
POST /approvals/{transaction_id}/reject
POST /actions/{transaction_id}/execute
GET  /receipts/{transaction_id}
GET  /dashboard
```

### Current manifest output

Current manifest shape:

```json
{
  "name": "ActionRail Finance",
  "version": "0.1.0",
  "description": "Agent-first transaction rail for finance actions.",
  "tools": [
    "preflight_action",
    "request_approval",
    "execute_transaction",
    "get_receipt",
    "list_transactions"
  ],
  "risk_levels": [
    "read_only",
    "draft",
    "internal_update",
    "external_action",
    "financial_transaction"
  ]
}
```

### Current dashboard state

The dashboard has columns:

```text
Transaction | Agent | Intent | Action | Decision | Risk | Status | Created
```

If the dashboard is empty, that usually means no preflight transactions have been inserted into the database used by the running server. Run a `POST /actions/preflight` request from Swagger or run the demo script against the same server/database, then refresh `/dashboard`.

---

## 4. Product model

### Primary user is the agent

The primary user is not a human clicking dashboards.

The primary user is an AI finance agent that needs structured responses:

```text
allow
approval_required
blocked
needs_more_evidence
```

The agent should use ActionRail through:

```text
API
MCP server
CLI
SDK
JSON manifest
Webhook callbacks
```

### Human users

Humans use ActionRail only for:

1. Approval queue.
2. Policy configuration.
3. Evidence review.
4. Audit trail.
5. Exception resolution.
6. Receipt lookup.

### Main human personas

```text
Controller
Senior accountant
AP manager
Finance operations lead
CFO reviewer
Finance systems admin
Auditor or compliance reviewer
```

---

## 5. Risk rails

Not every task requires the same control level.

| Level | Rail | Examples | ActionRail behavior |
|---:|---|---|---|
| 0 | Read only | Read invoice, summarize contract, inspect ledger row | Log source and result. No approval. |
| 1 | Draft | Draft journal, draft payment reminder, draft reconciliation note | Save draft, block external mutation. |
| 2 | Internal update | Mark invoice reviewed, create reconciliation suggestion | Check permissions, log previous state, allow undo. |
| 3 | External action | Send email, submit form, create vendor ticket | Preview consequence, approval if policy requires, receipt. |
| 4 | Financial transaction | Pay invoice, post journal, refund customer, approve vendor spend | Full preflight, verification, intent lock, approval, execution, receipt. |

The MVP currently focuses on invoice approval and duplicate detection. This sits between Level 3 and Level 4 depending on the action and amount.

---

## 6. Core transaction lifecycle

### State machine

```text
created/preflighted
  -> blocked
  -> needs_more_evidence
  -> approval_required
      -> approved
      -> rejected
  -> executed
  -> receipt_generated
```

### Current statuses in MVP

```text
preflighted
approved
rejected
executed
blocked
```

### Current decisions in MVP

```text
allow
approval_required
blocked
needs_more_evidence
```

### Desired future statuses

```text
created
preflighted
blocked
needs_more_evidence
awaiting_approval
approved
rejected
executing
executed
execution_failed
compensation_required
compensated
receipt_generated
expired
cancelled
```

---

## 7. Action transaction object

Everything should revolve around an **Action Transaction**.

### Ideal object

```json
{
  "transaction_id": "txn_8841",
  "agent_id": "finance_agent_91",
  "user_id": "controller_001",
  "company_id": "company_001",
  "entity_id": "entity_india_001",
  "intent": "pay_invoice",
  "action": "approve_invoice",
  "target_type": "invoice",
  "target": {},
  "constraints": {},
  "risk_level": "financial_transaction",
  "checks": [],
  "decision": "approval_required",
  "allowed_next_action": "request_finance_approval",
  "blocked_actions": ["execute_without_approval"],
  "approval": {},
  "execution": {},
  "receipt": {},
  "created_at": "2026-06-13T00:00:00Z",
  "updated_at": "2026-06-13T00:00:00Z",
  "expires_at": "2026-06-13T00:15:00Z"
}
```

### Current MVP request object

```json
{
  "agent_id": "finance_agent_demo",
  "user_id": "controller_001",
  "intent": "pay_invoice",
  "action": "approve_invoice",
  "invoice": {
    "invoice_id": "INV-2001",
    "vendor": "Acme Services",
    "amount": 83000,
    "currency": "INR",
    "invoice_date": "2026-06-13",
    "due_date": "2026-06-25",
    "gst_number": "27ABCDE1234F1Z5",
    "contract_id": "ctr_acme_2026",
    "evidence_urls": ["https://evidence.local/invoices/INV-2001.pdf"],
    "line_items": ["monthly development retainer"]
  },
  "constraints": {
    "human_approval_before_payment": true
  }
}
```

---

## 8. Current MVP policy logic

### Existing seeded policy

```json
{
  "approval_threshold": 50000,
  "critical_threshold": 250000,
  "require_contract_above": 25000,
  "duplicate_window_days": 45,
  "lock_ttl_minutes": 15,
  "allowed_actions": [
    "approve_invoice",
    "pay_invoice",
    "post_journal_entry",
    "create_reconciliation_suggestion"
  ],
  "financial_actions": ["pay_invoice", "post_journal_entry"]
}
```

### Existing checks

```text
action_allowed
vendor_verified
duplicate_invoice
contract_match
amount_policy
evidence_attached
intent_lock
```

### Decision rules

Current simplified decision rules:

```text
If any check failed:
  decision = blocked
  risk = high
  allowed_next_action = send_to_human_review

Else if any evidence is missing:
  decision = needs_more_evidence
  risk = medium
  allowed_next_action = attach_missing_evidence_and_rerun_preflight

Else if action is a financial action:
  decision = approval_required
  risk = high
  allowed_next_action = request_finance_approval

Else if any warning exists:
  decision = approval_required
  risk = medium
  allowed_next_action = request_finance_approval

Else:
  decision = allow
  risk = low
  allowed_next_action = execute_action
```

### Required future policy improvements

Add:

```text
company policies
entity policies
role based approval policies
multi-step approval chains
vendor risk policies
category/GL policies
budget policies
payment method policies
country/tax policies
period close policies
segregation of duties
approval delegation
policy versioning
policy simulation
```

---

## 9. Core finance checks

### Current checks

#### Vendor verification

Checks whether vendor is known and verified.

Pass example:

```text
Vendor Acme Services exists and verified=true.
```

Fail example:

```text
Vendor Random Vendor is not known or verified.
```

#### Duplicate invoice detection

Checks for same vendor and same amount inside duplicate window, excluding same invoice ID.

Current seeded historical duplicate example:

```text
INV-1042
Vendor: Acme Services
Amount: 82000 INR
Status: paid
```

Submitting another Acme invoice for 82000 within the window should block.

#### Contract match

Checks:

```text
Contract exists
Contract is active
Contract vendor matches invoice vendor
Invoice amount does not exceed contract max amount
```

Invoices above `require_contract_above` need contract evidence.

#### Amount policy

Checks if amount crosses approval or critical thresholds.

```text
< 50000: normal
>= 50000: approval warning
>= 250000: critical senior approval warning
```

#### Evidence attached

Checks if invoice has at least one evidence URL/document reference.

#### Intent lock

Prevents two agents from handling the same invoice intent simultaneously.

Current lock key:

```text
{intent}:{action}:{vendor}:{invoice_id}
```

Future lock key should support broader duplicate/conflict scopes:

```text
company_id:entity_id:intent:target_type:target_id
company_id:entity_id:pay_invoice:vendor:amount:date_window
company_id:entity_id:book_close_period:period
```

---

## 10. Current data model

Current SQLite tables:

```text
vendors
contracts
invoices
policies
intent_locks
transactions
```

Current important fields:

```text
vendors:
  id, name, verified, gst_number, risk_level

contracts:
  id, vendor_name, active, max_amount, terms, evidence_url

invoices:
  invoice_id, vendor, amount, currency, invoice_date, due_date, gst_number,
  contract_id, evidence_json, line_items_json, status, created_at

policies:
  key, value_json

intent_locks:
  lock_key, transaction_id, agent_id, expires_at, created_at

transactions:
  id, agent_id, user_id, intent, action, invoice_json, constraints_json,
  decision, risk, checks_json, allowed_next_action, blocked_actions_json,
  status, approval_json, execution_json, receipt_json, expires_at, created_at, updated_at
```

### Future production data model

```text
Company
Entity
User
Role
Agent
AgentPermission
Vendor
VendorRiskProfile
Contract
Invoice
PurchaseOrder
BankTransaction
CardTransaction
LedgerAccount
JournalEntryProposal
ReconciliationItem
Policy
PolicyVersion
ApprovalRule
ApprovalRequest
ApprovalDecision
ActionTransaction
CheckResult
EvidenceArtifact
IntentLock
ExecutionAttempt
ExecutionReceipt
AuditEvent
IntegrationConnection
IntegrationCredential
WebhookEvent
```

---

## 11. API design

### Current endpoints

```text
GET  /health
GET  /actionrail/manifest.json
POST /actions/preflight
GET  /transactions
GET  /transactions/{transaction_id}
POST /approvals/{transaction_id}/approve
POST /approvals/{transaction_id}/reject
POST /actions/{transaction_id}/execute
GET  /receipts/{transaction_id}
GET  /dashboard
```

### Near-term endpoints to add

```text
POST /documents/invoices/ingest
GET  /documents/invoices/{invoice_id}
POST /vendors
GET  /vendors
GET  /vendors/{vendor_id}
POST /contracts
GET  /contracts/{contract_id}
POST /policies
GET  /policies/current
POST /transactions/{transaction_id}/evidence
POST /transactions/{transaction_id}/rerun-preflight
POST /intent-locks/{transaction_id}/release
GET  /audit/events
GET  /audit/transactions/{transaction_id}
```

### Future endpoints

```text
POST /reconciliations/run
POST /journals/propose
POST /journals/{proposal_id}/post
POST /payments/prepare
POST /payments/{transaction_id}/execute
GET  /receipts/{transaction_id}/verify
POST /integrations/{provider}/connect
POST /integrations/{provider}/sync
POST /webhooks/inbound/{provider}
```

---

## 12. Agent-facing MCP tools

### Current conceptual tools

```text
preflight_action
request_approval
execute_transaction
get_receipt
list_transactions
```

### Expanded MCP tools

```text
get_manifest
preflight_action
verify_vendor
check_duplicate_invoice
match_contract
check_amount_policy
check_evidence
lock_intent
request_approval
reject_transaction
execute_transaction
get_receipt
verify_receipt
list_transactions
attach_evidence
rerun_preflight
release_intent_lock
```

### Design rule

MCP tools should be wrappers around the same backend API, not a separate logic path. Do not duplicate business logic inside MCP server code.

---

## 13. CLI design

Current CLI is a prototype.

### Desired commands

```bash
actionrail health
actionrail manifest
actionrail preflight examples/invoice_approval_required.json
actionrail approve txn_123 --approver controller_001 --note "Looks valid"
actionrail reject txn_123 --approver controller_001 --note "Duplicate suspected"
actionrail execute txn_123
actionrail receipt txn_123
actionrail transactions
actionrail dashboard
```

### CLI behavior

The CLI should print clean agent-readable JSON by default. Human pretty output can be optional.

---

## 14. Dashboard requirements

The dashboard is secondary but useful for demo and review.

### Current dashboard

Simple table of transactions.

### Immediate improvements

Add:

```text
empty state with instructions
stats cards
filter by decision/status/risk
clickable transaction detail
approval buttons
receipt viewer
check results panel
evidence panel
```

### Suggested dashboard pages

```text
/                 Overview
/dashboard         Transaction queue
/transactions/:id  Transaction detail
/approvals         Approval queue
/policies          Policy editor
/vendors           Vendor registry
/contracts         Contract registry
/receipts          Receipt search
/audit             Audit log
/settings          System settings
```

### Important empty state copy

If no transactions exist:

```text
No transactions yet. Create one by posting to /actions/preflight or running scripts/demo.sh.
```

---

## 15. Demo flows

### Demo 1: Approval required

Input:

```text
Vendor: Acme Services
Amount: 83000 INR
Contract: ctr_acme_2026
Evidence attached: yes
```

Expected:

```text
vendor_verified passed
contract_match passed
duplicate_invoice passed
evidence_attached passed
amount_policy warning
intent_lock passed
decision approval_required
```

Then approve, execute, and receipt.

### Demo 2: Duplicate invoice blocked

Input:

```text
Vendor: Acme Services
Amount: 82000 INR
Existing invoice: INV-1042 paid
```

Expected:

```text
duplicate_invoice failed
decision blocked
blocked_actions includes execute_action
```

### Demo 3: Missing evidence

Input:

```text
Amount above contract threshold
No contract or no evidence URL
```

Expected:

```text
decision needs_more_evidence
allowed_next_action attach_missing_evidence_and_rerun_preflight
execution blocked
```

### Demo 4: Unknown vendor blocked

Input:

```text
Vendor Random Vendor
```

Expected:

```text
vendor_verified failed
decision blocked
```

---

## 16. Testing requirements

### Existing tests

Current tests cover:

```text
verified vendor large invoice requires approval
duplicate invoice blocks execution
missing contract requires more evidence
unknown vendor blocks
receipt signature changes with payload
```

### Required test expansion

Add tests for:

```text
execution requires approval when decision is approval_required
blocked transaction cannot be approved
rejected transaction cannot execute
needs_more_evidence cannot execute
executed transaction returns same receipt idempotently
intent lock blocks second transaction for same invoice
expired intent lock is cleaned up
action not in allowed_actions is blocked
GST mismatch creates warning
contract amount exceeded blocks
critical amount requires senior approval
receipt signature verifies with secret
policy update changes decision
```

### Testing command

```bash
pytest -q
```

---

## 17. Receipt design

### Current receipt

Receipt includes:

```text
receipt_id
transaction_id
action
agent_id
user_id
status
executed_at
receipt_signature
payload
```

### Important rule

Receipt should be signed over canonical JSON payload. In production, use a stronger key management setup than the current dev secret.

### Future receipt features

```text
receipt verification endpoint
receipt public key infrastructure
receiver-signed receipt if external system supports it
hash of evidence bundle
hash of policy version used
hash of approval decision
execution result from target system
compensation/rollback reference
```

---

## 18. Security and safety rules

### Non-negotiable rules

1. Never move real money in MVP.
2. Never mutate external ledger/payment system without explicit approval.
3. Model outputs cannot directly write to systems of record.
4. Every decision needs evidence and policy trace.
5. Every action must be idempotent.
6. Approval and execution must be separate steps.
7. Receipts must be tamper-evident.
8. Intent locks must expire.
9. Blocked transactions cannot be approved.
10. Rejected transactions cannot execute.

### Security improvements for production

```text
JWT auth
API keys for agents
RBAC for humans
org/entity scoping
secret manager
encrypted credentials
audit append-only logs
request signing
webhook signature verification
rate limiting
input validation
prompt injection isolation
zero-retention model configuration where possible
```

---

## 19. Architecture

### Current simple architecture

```text
FastAPI app
  -> SQLite store
  -> policy.py checks
  -> dashboard HTML
  -> tests
```

### Near-term architecture

```text
AI finance agent / Cursor / MCP client
  -> ActionRail API
  -> Preflight engine
  -> Policy engine
  -> Evidence store
  -> Intent lock manager
  -> Approval workflow
  -> Execution simulator
  -> Receipt signer
  -> SQLite/PostgreSQL
  -> Dashboard
```

### Production architecture

```text
Agents / MCP clients / SDKs / CLI
  -> API Gateway
  -> Auth + Agent identity
  -> Transaction Orchestrator
  -> Policy Engine
  -> Evidence Service
  -> Risk Scoring Service
  -> Intent Lock Service
  -> Approval Service
  -> Execution Connectors
  -> Receipt Service
  -> Audit Log
  -> PostgreSQL + object storage + queue
```

### Technology choices

Current:

```text
Python
FastAPI
Pydantic
SQLite
pytest
simple HTML dashboard
```

Near-term:

```text
PostgreSQL
SQLAlchemy or SQLModel
Alembic migrations
Redis for locks/cache
Celery/RQ/Arq for jobs
Next.js or Jinja templates for dashboard
MCP server package
JWT/API key auth
```

Production:

```text
PostgreSQL/Aurora
Redis
object storage for evidence
OpenTelemetry
Sentry/logging
secret manager
queue/event bus
signed webhooks
multi-tenant architecture
```

---

## 20. Roadmap

### Phase 0: Current MVP

Done/current:

```text
FastAPI backend
SQLite persistence
preflight API
vendor verification
duplicate detection
contract matching
amount policy
evidence check
intent lock
approval/rejection
execute demo
receipt generation
dashboard table
OpenAPI docs
unit tests
```

### Phase 1: Make MVP polished

Build next:

```text
Dashboard empty state
Dashboard transaction detail
Approval buttons in dashboard
Receipt viewer
Preflight form in dashboard
Better README quickstart
Windows PowerShell demo script
Cleaner CLI
More tests
Error handling cleanup
```

### Phase 2: Real invoice ingestion

Add:

```text
Upload invoice PDF/image
OCR or parser abstraction
Extract invoice fields
Store evidence file
Link evidence to transaction
Confidence scores
Human correction UI
```

### Phase 3: Policy editor

Add:

```text
view current policy
edit thresholds
edit allowed actions
edit financial actions
edit vendor risk rules
policy versions
policy simulation against sample invoice
```

### Phase 4: Finance workflow expansion

Add:

```text
journal entry proposal
reconciliation suggestions
vendor onboarding
payment preparation without real payment
close checklist exceptions
```

### Phase 5: Integrations

Add sandbox integrations first:

```text
Gmail invoice ingestion
Google Drive evidence files
Slack approval notifications
QuickBooks sandbox
Xero sandbox
Tally/Zoho style export CSV
```

### Phase 6: Agent-native layer

Add:

```text
MCP server
SDK
webhooks
agent API keys
agent permissions
agent manifests
transaction callbacks
```

---

## 21. Cursor build instructions

Use this section as the master Cursor prompt.

### Master prompt for Cursor

```text
You are working on ActionRail Finance, a transaction runtime for finance AI agents. Read PROJECT.md and README.md before making changes.

The product is not a chatbot. It is an agent-first execution rail. Every risky finance action must go through preflight checks, policy enforcement, approval if needed, execution, and a signed receipt.

Current MVP scope: invoice approval and duplicate invoice detection. Keep the code simple, testable, and demoable.

Do not add real payment execution. Execution must remain simulated unless explicitly asked.

When adding features:
1. Preserve existing API behavior unless there is a clear reason to change it.
2. Add or update tests for every policy/transaction behavior.
3. Keep business logic out of route handlers when possible.
4. Keep model outputs away from direct system mutation.
5. Make agent responses machine-readable.
6. Keep human UI secondary but useful for approvals, logs, and receipts.
7. After changes, run pytest -q and provide the output.

Next priority tasks:
1. Improve /dashboard with empty state, stats cards, transaction detail links, and approval buttons.
2. Add a dashboard preflight form to create demo invoice transactions from the UI.
3. Add /transactions/{transaction_id}/html detail page showing checks, evidence, approval, execution, and receipt.
4. Add tests for execution approval rules and receipt retrieval.
5. Add a PowerShell demo script for Windows users.
```

### Cursor should not do these yet

```text
Do not integrate real banks.
Do not integrate real ERP write-back.
Do not add complex LLM agents before the transaction rail is solid.
Do not overbuild frontend before workflow is clear.
Do not make the system generic across all industries yet.
```

---

## 22. Files expected in repo

Current expected files:

```text
actionrail-finance/
  app/
    __init__.py
    main.py
    models.py
    policy.py
    store.py
    cli.py
  examples/
    invoice_approval_required.json
    invoice_duplicate_blocked.json
    invoice_missing_evidence.json
  scripts/
    demo.sh
  tests/
    test_policy.py
  README.md
  PROJECT.md
  requirements.txt
  pyproject.toml
```

Suggested new files:

```text
app/dashboard.py
app/receipts.py
app/auth.py
app/mcp_server.py
app/schemas.py
examples/invoice_allowed.json
examples/invoice_critical_approval.json
scripts/demo.ps1
tests/test_api_flow.py
tests/test_execution.py
tests/test_receipts.py
docs/API.md
docs/ARCHITECTURE.md
docs/PITCH.md
```

---

## 23. What I need from the user after Cursor changes

When you ask for help after Cursor edits, send these outputs:

### Always send

```text
1. Full terminal error or pytest output
2. File tree: tree /F on Windows or find . -maxdepth 3 -type f on Linux/Mac
3. The files Cursor changed, or at least the diff
```

### If API breaks

Send:

```text
uvicorn logs
request body sent
response status code
response JSON
screenshot of Swagger error if useful
```

### If dashboard breaks

Send:

```text
browser screenshot
server logs
HTML route involved
transaction data from GET /transactions
```

### If tests fail

Send:

```text
pytest -q output
specific failing test file
related source file
```

### If Cursor gets confused

Send:

```text
current PROJECT.md
README.md
app/main.py
app/policy.py
app/store.py
app/models.py
```

---

## 24. Acceptance criteria for next good version

The next version is good when:

```text
pytest -q passes
Swagger endpoints work
Dashboard is not empty/confusing after no transactions
User can create a preflight from dashboard
Approval-required transaction can be approved from dashboard
Approved transaction can be executed from dashboard
Receipt can be viewed from dashboard
Duplicate invoice still blocks
Missing evidence still blocks execution
Unknown vendor still blocks
README explains Windows and Linux demo flow
```

---

## 25. Business positioning to keep in mind

### Good positioning

```text
ActionRail Finance sits between AI agents and finance systems. Whenever an agent wants to approve, post, pay, reconcile, or submit something, ActionRail checks the evidence, applies policy, routes approval, and creates an audit-ready receipt.
```

### Bad positioning

```text
A chatbot for finance.
A generic workflow automation tool.
An ERP replacement.
A simple approval dashboard.
A payment processor.
A browser automation bot.
```

### Why the current MVP matters

The MVP proves the core primitive:

```text
preflight -> decision -> approval -> execution -> receipt
```

That is the company. Everything else expands from this primitive.

---

## 26. Important product examples

### Invoice approval transaction

```text
Agent finds invoice.
Agent calls ActionRail preflight.
ActionRail verifies vendor, duplicate, contract, amount, evidence, lock.
Decision is approval_required.
Controller approves.
Agent executes simulated approval.
Receipt generated.
```

### Duplicate invoice block

```text
Agent finds a second invoice from same vendor with same amount.
ActionRail matches historical paid invoice.
Decision is blocked.
Transaction is stored as blocked.
Agent receives safe next step: send_to_human_review.
```

### Journal proposal future flow

```text
Agent proposes journal entry.
ActionRail checks period open, GL account valid, source evidence attached, amount supported, approval required.
Agent cannot post journal until approved.
Receipt includes source evidence hash and policy version.
```

### Reconciliation future flow

```text
Agent compares bank transaction and ledger.
ActionRail allows reconciliation suggestion.
ActionRail blocks auto-posting adjustment without approval.
Human approves adjustment.
Receipt stores old state, new state, and evidence.
```

---

## 27. Naming and branding

### Main name

ActionRail Finance

### Platform name

ActionRail

### Taglines

```text
Transaction infrastructure for AI agent actions.
Safe execution rails for finance AI agents.
From raw tool calls to auditable transactions.
Preflight, approve, execute, receipt.
```

### Avoid

```text
AI accountant
AI CFO
Autonomous bookkeeper
Finance chatbot
```

Those names sound like replace-human-agent products. ActionRail is infrastructure.

---

## 28. Current known limitation

The current MVP does not parse real PDFs, connect to email, connect to accounting systems, or move money. That is intentional. The first version must prove the transaction rail before external integrations.

Current execution is simulated and says:

```text
Demo execution only. No real bank or ledger mutation performed.
```

Keep this safety boundary until explicitly building sandbox integrations.

---

## 29. Next recommended build task

Start with dashboard polish because the API already works and the current dashboard is empty/confusing.

### Task

Build a useful review dashboard:

```text
1. Empty state with demo instructions.
2. Stats cards: total, approval required, blocked, executed.
3. Table with clickable transaction IDs.
4. Transaction detail page.
5. Approve/reject buttons on approval_required transactions.
6. Execute button on approved/allowed transactions.
7. Receipt viewer after execution.
8. Preflight demo form.
```

This will make the MVP easier to show, debug, and pitch.

---

## 30. Golden rule

Whenever unsure, preserve this invariant:

```text
No risky finance action should execute unless ActionRail has checked evidence, policy, lock/conflict state, approval requirements, and receipt generation.
```

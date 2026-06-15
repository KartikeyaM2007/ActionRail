# ActionRail Finance Demo Video Script

## Goal
To demonstrate ActionRail as a transaction rail infrastructure, proving that finance AI agents can safely act within a constrained boundary before mutating external ledgers or executing real payments.

## Setup before recording
1. Clean local environment:
   ```bash
   python scripts/reset_demo_db.py
   ```
2. Have sample invoices ready (e.g., from `data/datasets/kaggle-invoices-sample/`).
3. Start the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## Recording checklist
- [ ] Screen resolution set to 1080p (or 1440p scaled).
- [ ] Browser zoom at 100%.
- [ ] Microphone check.
- [ ] No personal notifications visible.
- [ ] Demo terminal ready to show `pytest -q` locally before/after.

## 2 to 3 minute narration
"ActionRail Finance sits between your AI finance agents and the external systems they touch. When agents execute transactions, they need a safe transaction rail—a layer that enforces policy, checks for duplicates, handles approval workflows, and issues signed receipts, before mutating external databases. Here is a demonstration of how the core primitive works end-to-end, executing locally with simulated accounting writebacks."

## Scene-by-scene flow

### 1. Login
- Navigate to `/login`.
- Login as `controller@example.local`.

### 2. Dashboard
- Display the clean, neo-brutalist control plane.
- Emphasize the stats showing active workflow items.

### 3. Upload/review invoice
- Navigate to upload invoice.
- Upload an invoice from the dataset.
- Show the review screen; briefly manually correct a field if necessary.
- Submit the invoice to initiate the transaction.

### 4. Preflight decision
- Show the transaction detail view.
- Highlight the 7 checks that just ran (`action_allowed`, `duplicate_invoice`, `amount_policy`, etc.).
- Point to the `approval_required` decision. This represents the API response to the agent.

### 5. Approval workflow
- Show the Maker-Checker controls. The Controller cannot approve their own submission.

### 6. Maker-checker concept
- Log out, log in as `approver@example.local`.
- Navigate to the pending transaction.
- Click **Approve**.

### 7. Simulated execution
- Log out, log in as `executor@example.local`.
- Click **Execute**. The state becomes Executed.

### 8. Signed receipt
- Click **View Receipt**.
- Highlight the HMAC-SHA256 signature and the canonical JSON payload ensuring tamper evidence.

### 9. Accounting sandbox writeback
- Click the **Accounting Sandbox Writeback** link on the transaction detail.
- Emphasize this is a local draft and no external ERP was called.

### 10. Evidence pack
- Log out, log in as `auditor@example.local` to show RBAC isolation.
- Open the transaction detail and click **Download Evidence Pack**.
- Mention it produces a complete offline audit ZIP.

### 11. Replay
- Click the **Replay Audit** button.
- Show the simulation against current policies, demonstrating it's purely read-only memory generation.

### 12. Risk monitor
- Navigate to `/dashboard/risk`.
- Highlight operational metrics, authentication failures, and API limit warnings.

### 13. Audit log
- End by navigating to `/dashboard/audit`.
- Show the persistent, chronological ledger of all events across the lifecycle.

## What to click
Follow the "Scene-by-scene flow" exactly. Navigate menus clearly, allowing a brief pause before major actions (Approve, Execute, Download Evidence).

## What to say
Focus on the structural integrity. "Notice how a blocked transaction has no execute button. Notice the separation of duties preventing the creator from approving."

## Safety boundary lines to mention
"This is a local execution control plane."
"Execution is completely simulated here."
"No real money moves and no external APIs are called."

## Closing pitch
"Finance AI needs strong structural guardrails. ActionRail provides the runtime to make sure agents do the right thing, enforce your policies, and leave an auditable receipt behind. Thank you."

## Retake checklist
If any of these occur, restart the recording:
- Stumbled heavily on narration.
- Unexpected error page.
- Leftover data from a previous recording.
- Forgot to switch user roles during the approval/execution phases.

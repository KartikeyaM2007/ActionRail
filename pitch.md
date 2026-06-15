# ActionRail Live Pitch + Demo Script

## 0. Before meeting

Run:

```powershell
python scripts/reset_demo_db.py
uvicorn app.main:app --reload
```

Open browser tabs:

```text
http://127.0.0.1:8000/login
http://127.0.0.1:8000/dashboard
http://127.0.0.1:8000/docs
```

Keep terminal ready.

---

## 1. Opening pitch

Say:

“ActionRail Finance is a finance action gateway for AI agents.

The problem is simple: agents are starting to use tools, APIs, and automations. But in finance, we cannot let an agent directly pay invoices, write to ERP, or mutate accounting records.

So ActionRail sits between the agent and the finance system.

The agent requests a finance action through ActionRail. ActionRail checks policy, vendor status, contract evidence, duplicate risk, approval rules, and audit requirements. Then it returns a controlled decision: allowed, blocked, needs evidence, or approval required.

Humans do not use this as a normal finance dashboard. Humans use it as the control plane for approval, audit, risk, and policy.”

---

## 2. Show the agent side first

Say:

“Now I’ll act like an AI invoice agent. The agent wants to process a payment request, but before doing anything dangerous, it calls ActionRail.”

Run this in terminal:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/actions/preflight" `
  -Method POST `
  -ContentType "application/json" `
  -Headers @{
    "Idempotency-Key" = "live-demo-004"
  } `
  -Body (Get-Content ".\examples\invoice_approval_required.json" -Raw)
```

Say:

“This response is the important part. The agent gets a transaction ID, a decision, risk level, checks, and the next allowed action. The agent is not free to continue blindly.”

Copy the transaction ID from the response.

---

## 3. Show human control plane

Go to:

```text
http://127.0.0.1:8000/dashboard
```

Refresh.

Say:

“Now the same agent-created transaction appears in the human control plane. This is where finance users inspect what the agent requested.”

Click the transaction.

Point out:

```text
decision
risk
policy checks
invoice details
workflow state
allowed next action
audit trail
```

Say:

“This is not just logging. ActionRail is converting an agent request into a governed transaction.”

---

## 4. Show approval control

Login as approver, or use the available demo approver account from your README.

Say:

“This transaction requires approval because the policy says high-value finance actions cannot proceed automatically.”

Click approve.

Say:

“The agent cannot bypass this step. Approval is enforced by ActionRail.”

If maker-checker appears, say:

“Also notice maker-checker separation. The same actor cannot create and approve sensitive finance actions.”

---

## 5. Show execution simulation

Login as executor.

Open the same transaction.

Click execute.

Say clearly:

“This is simulated execution. No real money moves. In a production version, this is where a controlled ERP, bank, or payment connector would sit. But this prototype intentionally does not connect to real finance systems.”

---

## 6. Show signed receipt

Click View Receipt.

Say:

“After execution, ActionRail creates a signed receipt. This gives both the agent and auditor proof of what happened.”

Point to:

```text
receipt id
transaction id
status
signature
canonical payload
```

Say:

“This is the difference between an agent saying ‘I did it’ and the system producing a verifiable record.”

---

## 7. Show evidence pack

Login as auditor.

Open the transaction.

Click evidence pack download.

Say:

“For audit, ActionRail can export an evidence pack. This includes transaction context, decision trail, receipt data, policy state, and audit metadata.”

Say:

“This is local export only, not production immutable storage. But it demonstrates the compliance workflow.”

---

## 8. Show replay

Open the replay page.

Say:

“Replay lets an auditor reconstruct the policy decision later without changing any state. It is read-only.”

Say:

“This matters because finance teams need to know not only what happened, but why the system allowed, blocked, or escalated it.”

---

## 9. Show risk monitor

Go to:

```text
http://127.0.0.1:8000/dashboard/risk
```

Say:

“This is the risk view. It shows blocked actions, approval issues, API failures, idempotency conflicts, policy changes, evidence exports, and high-risk events.”

Say:

“So this is not only a transaction tool. It is an operations layer for agentic finance activity.”

---

## 10. Show audit log

Open audit log.

Say:

“Every sensitive step is recorded: login, approval, execution, evidence export, replay, risk monitor access, and authorization failures.”

Say:

“This gives a full trail across agent action and human control.”

---

## 11. Show agent integration files

Open these files briefly:

```text
docs/AGENT_INTEGRATION.md
examples/agent_client.py
examples/langgraph_actionrail_tool.py
examples/openapi_tool_schema.json
```

Say:

“These files show how a real agent system would integrate. A LangGraph, OpenAI tool, Bedrock-style agent, or automation workflow can call ActionRail as a tool before attempting finance actions.”

---

## 12. Closing pitch

Say:

“So the core idea is:

Agents should not directly perform finance actions.

They should request finance actions through a control gateway.

ActionRail turns agent requests into governed transactions with policy checks, human approval, maker-checker controls, simulated execution, signed receipts, replay, evidence packs, and risk monitoring.

This project is a complete local prototype of that control layer. It is not production SaaS yet, but it demonstrates the full end-to-end architecture.”

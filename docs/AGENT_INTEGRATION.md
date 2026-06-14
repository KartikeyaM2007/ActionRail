# Agent Integration Guide

This guide details how AI agents, autonomic workflows, and LLM-based systems integrate with **ActionRail Finance**.

> [!IMPORTANT]
> **ActionRail is not a human finance dashboard.**
> ActionRail is a finance action gateway for AI agents. The dashboard is the human control plane.
> Agents call the JSON API. Humans approve, audit, configure policy, and inspect risk.

---

## Mental model

In a typical agentic workflow, an AI agent determines that a financial action (like paying an invoice) needs to be taken. In traditional setups, the agent calls a direct payment tool. This is highly risky, as agents can hallucinate, duplicate calls, or execute transactions that violate corporate policy.

ActionRail introduces a **transaction control plane**:

```text
┌─────────────────┐             POST /actions/preflight            ┌──────────────────┐
│                 │ ─────────────────────────────────────────────► │                  │
│    AI Agent     │                                                │    ActionRail    │
│                 │ ◄───────────────────────────────────────────── │                  │
└─────────────────┘              Decision + Txn ID                 └────────┬─────────┘
                                                                            │ Enforces policy & checks
                                                                            ▼
┌─────────────────┐                                                ┌──────────────────┐
│  ERP / Ledger / │ ◄───────────────────────────────────────────── │   Human Review   │
│   Payment API   │             POST /actions/{id}/execute         │ (If required by  │
└─────────────────┘               (Only when allowed/approved)     │  policy rules)   │
                                                                   └──────────────────┘
```

> [!CRITICAL]
> **Rule**: Agents should never directly pay, write to ERP, or mutate accounting systems. They should request a controlled ActionRail transaction first.

---

## Agent-facing API

The primary surface of ActionRail is its JSON API. The main agent-facing endpoints are:

* `POST /actions/preflight` - Submit an invoice or finance action for validation.
* `GET /transactions/{transaction_id}` - Retrieve transaction status and current lifecycle step.
* `POST /actions/{transaction_id}/execute` - Execute the simulated action (only permitted if the transaction is `allowed` or `approved`).
* `GET /receipts/{transaction_id}` - Download the tamper-evident, HMAC-signed transaction receipt.

---

## Human control plane

The dashboard exists solely as a secondary helper for:
1. **Human-in-the-Loop Approvals**: When a preflight requires manual checker authorization, a controller or approver signs in to approve the transaction.
2. **Audit & Replay**: Auditors review the persistent transaction ledger and perform policy replays.
3. **Risk Monitoring**: Security events, authentication failures, and rate limits are visualised.
4. **Policy Configuration**: Admins configure amount thresholds, active vendors, and contracts.

---

## Basic agent flow

An agent follows this structured lifecycle to process any financial action:

1. **Preflight**: Send a `POST` request to `/actions/preflight` containing the action payload and invoice details.
2. **Handle Decision**: Read the returned `decision` and proceed according to the decision handling rules.
3. **Wait/Poll (if needed)**: If the decision is `approval_required`, monitor the transaction status (via polling or webhook) until a human changes it to `approved`.
4. **Execute**: Submit a `POST` request to `/actions/{id}/execute` to complete the transaction.
5. **Collect Receipt**: Fetch the signed receipt from `/receipts/{id}` to store as immutable proof of execution.

---

## Decision handling

ActionRail returns one of four deterministic decisions at preflight. The agent must handle each case structurally:

| Preflight Decision | Meaning | Agent Action |
|---|---|---|
| `allow` | Transaction passes all policy checks. | Agent can call `/execute` immediately. |
| `approval_required` | Above approval threshold or requires sign-off. | Agent must wait/notify humans to approve on the dashboard. |
| `blocked` | Fails a critical check (e.g., duplicate, blocked vendor). | Agent **must abort** and report the failure. |
| `needs_more_evidence` | Missing contract or required invoice evidence. | Agent must locate and upload evidence before retrying. |

---

## Idempotency

To prevent duplicate execution from network retries or agent loop errors, the agent **must** include an `Idempotency-Key` header on all mutation requests (`POST /actions/preflight` and `POST /actions/{id}/execute`).

* If ActionRail receives a request with a key it has already processed, it returns the cached response.
* If a different payload is sent with an identical key, a `409 Conflict` is returned.

---

## API key scopes

API clients are granted scoped permissions to ensure least-privilege security:

* `preflight:create` - Permits submitting preflight actions.
* `transactions:read` - Permits checking transaction status.
* `receipts:read` - Permits fetching signed receipts.

---

## What the agent must never do directly

AI agents must be structurally isolated from executing mutations on:
* **Bank accounts or payment rails** (Stripe, TransferWise, bank APIs).
* **Accounting sandboxes or production ledgers** (QuickBooks, Xero, Tally).
* **ERP records** (NetSuite, SAP).

All these systems are locked behind ActionRail's execution barrier. The agent only calls ActionRail, and ActionRail orchestrates the downstream mutation when safety rules are satisfied.

---

## Example tool description

When exposing ActionRail to an LLM agent via function calling or tool selection, use the following description to ensure correct model usage:

```json
{
  "name": "request_finance_action_preflight",
  "description": "Before attempting any finance action, create an ActionRail preflight transaction and return the policy decision, risk, checks, and next allowed action."
}
```

---

## Example integration patterns

Agents integrate with ActionRail in one of three ways:

1. **Straight-through Processing (STP)**:
   * Preflight → Returns `allow` → Agent immediately executes → Agent retrieves signed receipt.
2. **Human-in-the-loop (HITL) Gating**:
   * Preflight → Returns `approval_required` → Agent pauses the workflow and sends a Slack alert or dashboard notification to a human → Controller approves → Agent resumes and executes.
3. **Evidence Collection Retry**:
   * Preflight → Returns `needs_more_evidence` → Agent extracts contract ID or invoice attachment, links the evidence, and submits a new preflight.

---

## Safety boundary

* **Simulated Execution**: The execution step is simulated in this prototype.
* **Demo Receipt Payload**: The HMAC signature covers a payload marked with: `Demo execution only. No real bank or ledger mutation performed.`
* **Local Scope**: No actual bank mutations or external ERP calls occur in this prototype.

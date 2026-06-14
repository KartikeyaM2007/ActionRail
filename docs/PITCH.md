# ActionRail Finance — Pitch

## One-liner

**ActionRail turns risky finance agent actions into safe, auditable transactions.**

---

## Problem

AI agents are starting to perform real finance work — reading invoices, drafting journal entries, suggesting reconciliations, initiating payments. Today that work is wired as raw tool calls:

```text
agent → call tool → action happens
```

That is unsafe for finance.

- A duplicate invoice goes out the door because no deduplication ran.
- A payment executes without approval because the policy was in a prompt.
- An audit trail is missing because nothing generated a receipt.
- Two agents conflict on the same invoice because no intent lock existed.

Finance teams already have controls: thresholds, approval chains, evidence requirements, duplicate windows, segregation-of-duties rules, signed records. Encoding all of that in every agent's system prompt is brittle, non-auditable, and doesn't scale. There is no dedicated execution layer that sits between AI agents and finance systems and enforces those controls deterministically.

## Solution

ActionRail is a **transaction runtime for AI agent actions**. Every meaningful agent action becomes an explicit transaction with a lifecycle:

```text
agent → preflight → verify evidence → apply policy → lock intent
      → decision → approval if required → execute → signed receipt
```

An agent calls `POST /actions/preflight` and receives one of four structured decisions:

| Decision | Meaning |
|---|---|
| `allow` | All checks passed. Agent may proceed directly. |
| `approval_required` | Checks passed but policy requires human sign-off before execution. |
| `blocked` | A check failed. Agent must not proceed. Evidence of failure is included. |
| `needs_more_evidence` | A required document or contract reference is missing. |

These decisions are deterministic. They do not come from an LLM. The agent integrates with them the same way it integrates with an HTTP status code.

Approval and execution are separate steps. A blocked transaction cannot be approved. A rejected transaction cannot execute. These are hard state guards enforced in the transaction store, not model outputs.

Every successful execution produces an HMAC-SHA256 signed receipt over the canonical JSON payload — verifiable by any party with the key, with no dependency on ActionRail being online.

## What the current MVP proves

The MVP demonstrates the full primitive end-to-end:

1. An agent submits an invoice preflight. ActionRail runs seven checks (`action_allowed`, `vendor_verified`, `duplicate_invoice`, `contract_match`, `amount_policy`, `evidence_attached`, `intent_lock`) and returns a structured decision.
2. A duplicate invoice from the same vendor at the same amount is **blocked before execution** — the agent receives the conflicting invoice as evidence.
3. A large invoice without a contract reference is **gated for evidence** — execution is blocked until it is attached.
4. A valid above-threshold invoice is **held for human approval** — the agent receives `approval_required` and cannot execute until a controller approves.
5. After approval and execution, ActionRail produces a **tamper-evident HMAC-signed receipt** with the decision trace, approval reference, and execution timestamp.
6. A real invoice image or PDF can be **uploaded directly from the browser**. ActionRail runs OCR (optional), extracts fields, and shows a review screen where a human confirms every value before a transaction is created. This prevents creating transactions from untrusted OCR guesses.
7. After simulated execution, ActionRail produces a **local accounting sandbox writeback**: a draft bill JSON and audit packet JSON stored on disk. This proves the accounting writeback boundary — the same boundary where a real integration (QuickBooks, Xero, Tally, Zoho) would be wired in later phases.

The primitive is proved when the three demo flows all behave correctly **and** the full upload lifecycle completes from invoice image through OCR, review, approval, execution, receipt, and accounting writeback. That is what this MVP is for.

**Safety boundary:** Execution is simulated — no real payments, no bank/ERP integration, no real money movement. The accounting sandbox writeback is local-only: no ERP, bank, or ledger mutation is performed.

## Demo narrative

Three flows, three different parts of the rail:

| Flow | What it proves |
|---|---|
| **Approval Required Invoice** — Acme Services, ₹83,000, contract attached, evidence attached | Approval gating. A valid above-threshold invoice is held for sign-off. Full `preflight → approved → executed → receipt` lifecycle completes. |
| **Duplicate Invoice** — same vendor + amount as a previously-paid invoice | Duplicate blocking. ActionRail blocks the action before damage is possible. `decision=blocked`, no Execute button, conflicting invoice in evidence. |
| **Missing Evidence Invoice** — AWS, ₹12,000, no `evidence_urls` | Evidence gating. `needs_more_evidence`. Execution is blocked until evidence is attached. |

All three use the same backend engine an agent would call via the JSON API. The dashboard is just a way to see and interact with those transactions as a human reviewer.

## Why now

- Finance AI agents went from demos to production workflows in 2025–2026. The pressure to give them more autonomy is accelerating.
- Regulated industries cannot accept "the policy is in the prompt." They need deterministic, auditable enforcement.
- Existing AP automation and ERP tools were designed for human-initiated workflows. They do not expose agent-first primitives: machine-readable decisions, intent locks, structured receipts, manifest-based discovery.
- The cost of a wrong autonomous payment, a duplicate payout, or a missed approval is immediate and measurable — that is a clear buyer motivation.

## First wedge: invoice approval and duplicate detection

Invoice approval and duplicate detection were chosen because they exercise every check in the rail on the smallest possible scope:

- Vendor verification, duplicate detection, contract matching, amount policy, evidence check, intent lock, approval gating, state-guarded execution, signed receipt.
- The YC demo is concrete: block the duplicate before damage happens, approve the legitimate large invoice, get a real signed receipt.
- Every finance team already cares about duplicate invoices and approval thresholds. No education required.

## What is unique

**This is infrastructure, not a dashboard.** An approval dashboard is a UI. ActionRail is a protocol — a structured interface between AI agents and finance systems, with machine-readable decisions, signed receipts, and deterministic state guards. The dashboard is a way to see and interact with that protocol as a human.

**The transaction primitive, not the workflow tool.** Existing workflow and AP automation tools manage human-initiated approval flows. They were not designed to serve as a callable API layer for autonomous agents. ActionRail starts from the agent's perspective: what does a machine caller need to safely perform a finance action?

**All the controls, in one layer.** Vendor verification, deduplication, contract matching, evidence requirements, approval thresholds, intent locks, state guards, signed receipts — separately these exist in ERPs, AP tools, and internal systems. ActionRail combines them into a single callable layer an agent can integrate with in a few API calls.

**Deterministic, not probabilistic.** The decision logic is not a model. It is policy-driven code. `blocked` means blocked. The agent does not have to interpret a confidence score or hedge against hallucination. This is what regulated industries need.

**The safety boundary is codified, not promised.** The MVP's execution boundary is in the code and in every signed receipt payload: `Demo execution only. No real bank or ledger mutation performed.` Real integrations are deferred until explicitly built with production controls. This is a feature, not a limitation — it means the rail can be audited and reasoned about at each phase.

## Why this becomes bigger

The transaction primitive is vertical-agnostic. Finance is the hardest and most valuable first wedge, but the same lifecycle — preflight, policy check, approval gate, execution, signed receipt — applies wherever AI agents take high-risk actions:

- **Travel**: approve booking changes above policy thresholds.
- **HR**: gate offer letters and compensation changes with multi-approver chains.
- **Legal**: gate document execution and contract amendments.
- **DevOps**: require approval before destructive infrastructure changes.
- **Commerce**: enforce purchase limits and vendor onboarding rules for autonomous procurement agents.

Every vertical has the same pattern: high-value actions, policy requirements, audit obligations, human-in-the-loop checkpoints. ActionRail becomes the standard execution layer under all of them.

## Roadmap

- **Phase 2 — Real invoice ingestion**: PDF/image upload, OCR, evidence storage, confidence scores, human correction.
- **Phase 3 — Policy editor**: editable thresholds, allowed actions, vendor risk rules; policy versioning; policy simulation.
- **Phase 4 — Workflow expansion**: journal entry proposals, reconciliation suggestions, vendor onboarding, payment preparation (still no real execution).
- **Phase 5 — Sandbox integrations**: Gmail ingestion, Drive evidence, Slack approvals, QuickBooks / Xero / Tally / Zoho sandbox connectors. Sandbox first, always.
- **Phase 6 — Agent-native layer**: MCP server, SDK, webhooks, agent API keys, agent manifests, transaction callbacks.

The company is the primitive. Everything else extends from it.

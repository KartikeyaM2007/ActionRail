# Phase 5C Prompt — Approval Workflow Engine

Do not run this during the handoff pass.
This is saved for the next coding session.

Phase 5C: approval workflow engine, maker-checker controls, and separation of duties.

Add:
- `approval_workflows` table to track multi-step workflow state.
- `approval_steps` table to track individual steps within a workflow.
- An approval workflow planner that computes the necessary steps based on risk and policy rules.
- Automatic workflow creation on `approval_required` transactions during preflight.
- Maker-checker separation: block the user who uploaded the invoice or requested the transaction from approving it.
- Wrong-role denial: enforce exact role requirements for specific approval steps.
- Multi-step approval logic for high-risk/high-amount transactions.
- Rejection flow: any rejection aborts the entire workflow.
- Execution gating: execution is blocked until all approval steps are complete.
- Workflow audit events for every step transition.
- Transaction detail workflow section in the UI showing pending/completed steps.
- Tests to cover the new constraints and state transitions.
- Docs update.
- ForKnow update.

# GitHub Publishing Checklist

## Repo description
Local finance-agent execution control plane: preflight, approval workflows, simulated execution, signed receipts, evidence packs, replay, and risk monitoring.

## Suggested topics
ai-agents
agentic-ai
fintech
governance
audit
fastapi
sqlite
approval-workflows
risk-management
invoice-automation

## README check
- [ ] Ensure README explicitly states this is a "local prototype" and "no real money moves."
- [ ] Ensure the MVP scope aligns with current repository capabilities.
- [ ] Confirm links to `DEMO_VIDEO_SCRIPT.md`, `GITHUB_PUBLISHING.md`, and `SECURITY.md` are present.

## Screenshot checklist
- [ ] `docs/screenshots/README.md` canonical 17 screenshots are captured.
- [ ] No real PII or real financial data is visible in any screenshot.

## Demo video checklist
- [ ] Video recorded following `docs/DEMO_VIDEO_SCRIPT.md`.
- [ ] Safety boundary is audibly emphasized during narration.

## Secret hygiene
- [ ] No `.env` files are tracked.
- [ ] No real API keys, Stripe secrets, or ERP credentials exist in the codebase.
- [ ] All database seeds use `example.local` mock emails.

## Local files that must not be committed
- [ ] `actionrail.db`
- [ ] `data/uploads/*`
- [ ] `data/datasets/*`
- [ ] `data/contract_evidence/*`
- [ ] `data/audit_exports/*.json`
- [ ] `data/audit_exports/*.zip`
- [ ] `data/accounting_sandbox/**/*.json`
- [ ] `kaggle/kaggle.json`

## Before pushing public
- [ ] Run `pytest -q` to ensure 252 tests pass successfully.
- [ ] Run `git status --short` to ensure the working tree is clean.
- [ ] Choose and add a LICENSE before public release.

## After pushing public
- [ ] Add the repo description and topics to the GitHub UI.
- [ ] Pin the repository to your profile.

## Suggested pinned repo blurb
"ActionRail Finance: A transaction runtime for AI finance agents enforcing policy checks, approvals, and simulated execution before ledger mutation."

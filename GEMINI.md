# Antigravity Project Entry Rules

Before making changes, read these first:

1. AGENTS.md
2. docs/ANTIGRAVITY_HANDOFF.md
3. docs/ROUTE_MAP.md
4. docs/SCHEMA_MAP.md
5. ForKnow.md
6. HANDOFF.md
7. TASKS.md
8. CHANGELOG.md

Follow AGENTS.md as the primary project rule file.

Hard constraints:

- Do not add real payments.
- Do not add external ERP, bank, accounting, Gmail, Outlook, Slack, Stripe, Razorpay, QuickBooks, Xero, Zoho, or Tally integrations unless explicitly requested.
- Do not change JSON API response shapes.
- Do not change receipt signature payloads.
- Keep execution simulated.
- Run pytest before final response.
- Update ForKnow.md after every meaningful change.

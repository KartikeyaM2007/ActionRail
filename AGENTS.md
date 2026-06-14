# ActionRail Finance Agent Rules

# ActionRail Finance â€” repo rules

This is the project rule file for ActionRail Finance. It is always applied. Treat it as a hard constraint on top of `PROJECT.md`.

## 1. Read context before major edits

Before any non-trivial change such as a new endpoint, new check, schema change, dashboard rework, test rewrite, dependency change, or architecture change, read in this order:

1. `PROJECT.md` â€” product and architecture spec, source of truth.
2. `TASKS.md` â€” current goal and what is next.
3. `DECISIONS.md` â€” settled why-decisions, including what not to do.
4. `HANDOFF.md` â€” current state, run instructions, and what not to change.
5. `CHANGELOG.md` â€” previous changes.
6. `ForKnow.md` â€” latest work journal entries for ChatGPT handoff.

If any of these conflict with the user's request, surface the conflict before coding.

## 2. Stay agent-first, not chatbot-first

- The primary user is an AI agent.
- Responses must be machine-readable where applicable: `allow`, `approval_required`, `blocked`, `needs_more_evidence`.
- Do not reframe ActionRail as a chatbot, AI accountant, AI CFO, autonomous bookkeeper, or ERP replacement.
- The dashboard is secondary to API, MCP, and CLI. Polish it, but never let it become the product.
- Keep business logic in `app/policy.py` and `app/store.py`.
- Route handlers and HTML templates should orchestrate, not decide.
- The product is a transaction runtime for finance AI agent actions.

## 3. No real payment execution

- Execution stays simulated.
- Do not add real bank, ERP, payment-rail, Gmail, external finance API, or ledger writeback in this codebase.
- Preserve the demo-execution boundary message and the separation between approval and execution.
- Approval and execution must remain distinct steps.
- Blocked transactions cannot be approved.
- Rejected transactions cannot execute.
- `needs_more_evidence` transactions cannot execute.
- If the user explicitly asks for real payments, stop and confirm because this overrides `DECISIONS.md` D3 and requires a new decision entry.

## 4. Do not remove tests

- Never delete or weaken existing tests in `tests/` to make a change pass.
- Add new tests for every new policy or transaction behavior.
- If a test legitimately needs to change because behavior was intentionally updated, call that out explicitly in the response and in `CHANGELOG.md`.
- Keep the repo green unless the user explicitly asks for experimental broken work.

## 5. After every change: update HANDOFF.md and CHANGELOG.md

After every user-requested change, update:

### `HANDOFF.md`

Refresh:

- Current project state
- What changed
- How to run
- Important files touched
- What to do next
- Known issues
- What not to change, if it shifted

### `CHANGELOG.md`

Add an entry under a new dated heading.

Use sections as appropriate:

- Added
- Changed
- Fixed
- Removed
- Tests

If the change is purely docs, cleanup, or styling with no behavior impact, still note it briefly so the next chat can see what happened.

## 6. Mandatory Work Journal: ForKnow.md

`ForKnow.md` is mandatory.

It is not a normal internal handoff file. It is the user-facing work journal that the user will copy paste back to ChatGPT so ChatGPT knows exactly what Cursor actually did.

After every user-requested change, before giving the final response, append a new entry to `ForKnow.md`.

Rules:

- Always append a new entry.
- Never delete old entries.
- Never overwrite previous entries.
- Keep the entry factual.
- Do not exaggerate.
- Mention every file changed.
- Mention every test command run and exact output.
- Mention any errors, skipped tasks, assumptions, or incomplete work.
- Mention if tests were not run.
- Mention what still needs manual review.
- Keep the latest entry easy for the user to copy paste.
- If the task was only a rules/doc update, still append a `ForKnow.md` entry.
- If `ForKnow.md` does not exist, create it with a short header explaining its purpose, then append the latest entry.

Each new entry must use this format:

# Cursor Work Update: <short task name>

## Date

<date and time if available>

## Prompt I worked on

<brief summary of the user prompt>

## Files changed

| File | What changed |
|---|---|
| path/to/file | specific change |

## What I added

- ...

## What I modified

- ...

## What I did not change

- ...

## Tests run

```bash
<test command>
```

```text
<exact output>
```

If tests were not run, write:

```text
Tests not run yet.
```

## Current status

- App status:
- Dashboard status:
- API status:
- Known issues:

## What the user should send to ChatGPT

Copy paste this whole latest `ForKnow.md` entry.

## 7. Run pytest -q after backend changes

Any change to the following requires running:

```bash
pytest -q
```

Run it after changes to:

- `app/`
- `tests/`
- `requirements.txt`
- `pyproject.toml`
- database behavior
- policy behavior
- transaction behavior
- approval or execution behavior

Paste the exact output in:

1. Final response
2. `ForKnow.md`
3. `HANDOFF.md` if relevant
4. `CHANGELOG.md` under Tests if relevant

If tests fail, fix them in the same change or stop and report clearly. Do not leave the repo red without explicitly saying so.

## 8. Keep changes small and explain them

- Surgical edits only.
- Touch only what the task requires.
- Leave adjacent code, comments, and formatting alone unless needed.
- Match existing style even if you would write it differently.
- Remove only the imports, variables, or functions your own change orphaned.
- Do not sweep up pre-existing dead code unless asked.
- In the final response, list every changed file with a one-line reason.
- The user should be able to map every diff line back to the request.

## 9. Frontend and design rules

The current frontend is FastAPI server-rendered HTML plus static CSS.

Until explicitly changed:

- Do not migrate to Next.js.
- Do not add React.
- Do not add Tailwind.
- Do not add shadcn/ui.
- Do not add a frontend build pipeline.
- Use plain templates and centralized static CSS.

When applying the neo-brutalist design system:

- Keep it controlled and finance-grade.
- Use cream background `#FFFDF5`.
- Use pure black `#000000` for borders, text, and shadows.
- Use hot red `#FF6B6B` for blocked/risky actions.
- Use vivid yellow `#FFD93D` for approval required.
- Use soft violet `#C4B5FD` for draft/internal states.
- Use thick black borders.
- Use hard offset shadows.
- Use sharp corners.
- Use bold typography.
- Keep accessibility and contrast strong.
- Do not make the product look like a toy.
- Dashboard is for review, approvals, logs, receipts, and demo only.

## 10. Product boundaries

The MVP is currently:

- Invoice approval
- Duplicate invoice detection
- Missing evidence detection
- Policy checks
- Approval or rejection
- Simulated execution
- Signed receipt
- Basic dashboard
- Agent-facing API
- CLI/demo support

Do not expand into these yet unless explicitly asked:

- Real payment execution
- Bank integration
- ERP integration
- Gmail/Outlook integration
- Full accounting automation
- Autonomous CFO features
- Payroll
- Tax filing
- Real vendor onboarding
- Production authentication
- Production multi-tenant billing
- Next.js frontend migration

## 11. Final response requirements

Every final response after a change must include:

1. Summary of what was done
2. Files changed
3. Tests run and exact output
4. Whether `HANDOFF.md`, `CHANGELOG.md`, and `ForKnow.md` were updated
5. Any known issue or manual review needed
6. A reminder that the user can copy the latest `ForKnow.md` entry back to ChatGPT


---

# Karpathy behavioral guidelines

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" â†’ "Write tests for invalid inputs, then make them pass"
- "Fix the bug" â†’ "Write a test that reproduces it, then make it pass"
- "Refactor X" â†’ "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] â†’ verify: [check]
2. [Step] â†’ verify: [check]
3. [Step] â†’ verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.


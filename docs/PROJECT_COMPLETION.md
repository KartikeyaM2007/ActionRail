# ActionRail Finance — Project Completion Status

Honest assessment of where this repo stands as of Phase 4A.

This is a **real local MVP**, not a production finance system.

---

## MVP complete

The following are implemented and tested:

| Capability | Status |
|---|---|
| Invoice preflight via API | Done |
| Seven policy checks | Done |
| Four machine-readable decisions | Done |
| Duplicate invoice detection | Done |
| Intent locks | Done |
| Approval / rejection flow | Done |
| Simulated execution | Done |
| HMAC-SHA256 signed receipts | Done |
| Agent manifest endpoint | Done |
| Operational dashboard (demo buttons, queue, stats) | Done |
| Real invoice upload (PDF/PNG/JPG) | Done |
| Optional OCR-assisted extraction | Done |
| Review-before-transaction (two-step upload) | Done |
| Local accounting sandbox writeback | Done |
| Dashboard stat correctness (operational counts) | Done |
| Transaction detail UI state polish | Done |
| Demo reset script | Done |
| Release checklist + docs | Done |

**Test count:** 154+ passing (`pytest -q`).

---

## Manually verified

| Flow | Verified |
|---|---|
| Demo preflight (approval / duplicate / missing evidence) | Yes |
| Approve → execute → signed receipt | Yes |
| Real upload → review → transaction | Yes (browser) |
| Accounting sandbox writeback | Yes (browser) |
| Dashboard stats after execution | Yes |
| GitHub push | Completed by user |

---

## Tested

```bash
pytest -q
# 154 passed (as of Phase 4A)
```

Test coverage includes:

- Policy engine and receipt signing
- Dashboard routes and stat aggregation
- Upload/review flow (offline, no real OCR required)
- Accounting writeback idempotency
- API JSON shape preservation
- Demo DB reset script

Tests do **not** require internet, real ERP, live OCR, or committed invoice files.

---

## Safe boundaries

| Boundary | Enforced |
|---|---|
| No real payment execution | Yes — simulated only |
| No ERP/bank mutation | Yes — local sandbox JSON only |
| No external API calls for finance | Yes |
| Receipt demo boundary in signed payload | Yes |
| Upload files gitignored | Yes |
| DB gitignored | Yes |
| Kaggle credentials gitignored | Yes |
| Generated sandbox JSON gitignored | Yes |

See [`docs/SAFETY_BOUNDARY.md`](SAFETY_BOUNDARY.md).

---

## Known limitations

| Limitation | Notes |
|---|---|
| SQLite single-file DB | Not multi-tenant or HA |
| No production auth | Open local API |
| OCR optional | Manual field entry always available |
| Regex PDF extraction | Basic; not ML-based |
| Dashboard is secondary | API is the product |
| Screenshots | Capture flow documented; files may not be committed yet |
| No CI badge in README | Add when CI is configured |
| `app/cli.py` | Prototype — not fully polished |

---

## Future roadmap

Deferred intentionally (see `PROJECT.md` and `DECISIONS.md`):

1. Expand backend-policy test coverage (intent lock expiry, GST mismatch, etc.).
2. MCP server exposing manifest tools.
3. Production auth, RBAC, multi-tenant.
4. Real provider sandbox connectors (QuickBooks, Xero, Tally).
5. Email/document ingestion.
6. Managed OCR with confidence SLAs.
7. Production deployment (Postgres, object storage, secret manager).

---

## Before pinning the repo publicly

- [ ] Run [`docs/RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md)
- [ ] Capture screenshots per [`docs/screenshots/README.md`](screenshots/README.md) (optional for tests, recommended for demos)
- [ ] Add GitHub repo description and topics
- [ ] Optional: create a release tag (e.g. `v0.1.0-mvp`)

---

## Related documents

- [`docs/DEMO_SCRIPT.md`](DEMO_SCRIPT.md) — 2–3 minute walkthrough
- [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) — system design
- [`docs/SAFETY_BOUNDARY.md`](SAFETY_BOUNDARY.md) — what is and is not real
- [`docs/RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) — pre-push checklist

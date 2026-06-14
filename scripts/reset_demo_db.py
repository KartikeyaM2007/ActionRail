"""Reset the local ActionRail Finance demo SQLite database.

Local-only. Drops the project's own tables and re-runs `init_db` + `seed_demo`
so a fresh demo recording starts from a known clean state.

This script:
  - touches ONLY the SQLite file at `app.store.DB_PATH`
  - never deletes arbitrary files
  - never connects to any external system

Recommended usage:

    # 1. Stop uvicorn if it's running.
    # 2. Reset the demo DB:
    python scripts/reset_demo_db.py
    # 3. Restart the app:
    uvicorn app.main:app --reload
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make the project root importable when run as `python scripts/reset_demo_db.py`.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.store import DB_PATH, connect, init_db, seed_demo  # noqa: E402

# Tables this project owns. Listed in dependency-safe order (children first).
PROJECT_TABLES: tuple[str, ...] = (
    "api_request_events",
    "idempotency_records",
    "api_clients",
    "evidence_exports",
    "audit_events",
    "contract_evidence",
    "accounting_writebacks",
    "approval_steps",
    "approval_workflows",
    "intent_locks",
    "transactions",
    "uploaded_documents",
    "invoices",
    "contracts",
    "vendors",
    "policies",
    "users",
)


def reset(db_path: Path | str | None = None) -> Path:
    """Drop project tables and re-seed. Returns the path that was reset."""
    target = Path(db_path) if db_path else DB_PATH
    conn = connect(target)
    try:
        for table in PROJECT_TABLES:
            conn.execute(f"DROP TABLE IF EXISTS {table}")
        conn.commit()
        init_db(conn)
        seed_demo(conn)
    finally:
        conn.close()
    return target


def main() -> None:
    print("ActionRail Finance — demo DB reset")
    print(f"Target: {DB_PATH}")
    target = reset()
    print(f"  ✓ Dropped project tables: {', '.join(PROJECT_TABLES)}")
    print("  ✓ Schema recreated.")
    print("  ✓ Seed data loaded (vendors, contracts, default policy, demo users, INV-1042 historical invoice).")
    print(f"Done. Reset {target}.")
    print("If uvicorn was running with --reload, restart it to see a clean queue.")


if __name__ == "__main__":
    main()

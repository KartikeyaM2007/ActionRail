"""Tests for `scripts/reset_demo_db.py`. Uses a tmp DB; never touches the real one."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from app.store import connect, init_db, seed_demo

_ROOT = Path(__file__).resolve().parent.parent


def _load_reset_module():
    spec = importlib.util.spec_from_file_location(
        "reset_demo_db",
        _ROOT / "scripts" / "reset_demo_db.py",
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_reset_clears_transactions_and_keeps_seed(tmp_path: Path):
    target = tmp_path / "demo.db"

    # Seed a DB with the normal demo schema and add a fake transaction so we can
    # prove the reset removed it.
    conn = connect(target)
    init_db(conn)
    seed_demo(conn)
    conn.execute(
        "INSERT INTO transactions(id, agent_id, user_id, intent, action, invoice_json, "
        "constraints_json, decision, risk, checks_json, allowed_next_action, "
        "blocked_actions_json, status, expires_at, created_at, updated_at) "
        "VALUES ('txn_x', 'a', 'u', 'i', 'act', '{}', '{}', 'allow', 'low', "
        "'[]', 'execute_action', '[]', 'preflighted', '2099-01-01', '2099-01-01', '2099-01-01')"
    )
    conn.commit()
    assert conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0] == 1
    conn.close()

    mod = _load_reset_module()
    returned_path = mod.reset(db_path=target)
    assert Path(returned_path) == target

    fresh = connect(target)
    # Transactions table is empty after reset.
    assert fresh.execute("SELECT COUNT(*) FROM transactions").fetchone()[0] == 0
    # Seeded vendors / contracts / policies / historical invoice are present.
    assert fresh.execute("SELECT COUNT(*) FROM vendors").fetchone()[0] >= 3
    assert fresh.execute("SELECT COUNT(*) FROM contracts").fetchone()[0] >= 2
    assert fresh.execute("SELECT COUNT(*) FROM policies").fetchone()[0] >= 1
    assert fresh.execute(
        "SELECT 1 FROM invoices WHERE invoice_id='INV-1042'"
    ).fetchone() is not None
    fresh.close()


def test_reset_is_idempotent_on_a_fresh_db(tmp_path: Path):
    target = tmp_path / "demo.db"
    mod = _load_reset_module()
    # Resetting a non-existent DB should still produce a seeded one.
    mod.reset(db_path=target)
    mod.reset(db_path=target)  # second call must not error
    conn = connect(target)
    assert conn.execute("SELECT COUNT(*) FROM vendors").fetchone()[0] >= 3
    conn.close()

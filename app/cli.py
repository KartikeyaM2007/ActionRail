from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.models import PreflightRequest
from app.policy import run_preflight
from app.store import connect, init_db, seed_demo


def main() -> None:
    parser = argparse.ArgumentParser(description="ActionRail Finance CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    preflight = sub.add_parser("preflight", help="Run preflight on a JSON request file")
    preflight.add_argument("file", type=Path)

    args = parser.parse_args()
    conn = connect()
    init_db(conn)
    seed_demo(conn)

    if args.command == "preflight":
        data = json.loads(args.file.read_text(encoding="utf-8"))
        req = PreflightRequest(**data)
        result = run_preflight(conn, req)
        print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

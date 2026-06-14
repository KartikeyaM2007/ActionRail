#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://127.0.0.1:8000}"

printf "\n--- Health ---\n"
curl -s "$BASE/health" | python -m json.tool

printf "\n--- Preflight: approval required ---\n"
TXN=$(curl -s -X POST "$BASE/actions/preflight" \
  -H 'Content-Type: application/json' \
  --data-binary @examples/invoice_approval_required.json | tee /tmp/actionrail-preflight.json | python -c "import json,sys; print(json.load(sys.stdin)['transaction_id'])")
cat /tmp/actionrail-preflight.json | python -m json.tool

printf "\n--- Approve transaction $TXN ---\n"
curl -s -X POST "$BASE/approvals/$TXN/approve" \
  -H 'Content-Type: application/json' \
  -d '{"approver_id":"controller_001","note":"Approved after evidence review"}' | python -m json.tool

printf "\n--- Execute transaction $TXN ---\n"
curl -s -X POST "$BASE/actions/$TXN/execute" | python -m json.tool

printf "\n--- Preflight: duplicate blocked ---\n"
curl -s -X POST "$BASE/actions/preflight" \
  -H 'Content-Type: application/json' \
  --data-binary @examples/invoice_duplicate_blocked.json | python -m json.tool

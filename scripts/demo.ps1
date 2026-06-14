# ActionRail Finance — guided Windows PowerShell demo
#
# Safe and non-destructive. Prints what to do, runs pytest, and shows the
# next commands you'll want to copy/paste yourself. Does NOT auto-launch
# uvicorn (long-running) or auto-reset the demo DB (destructive).
#
# Usage from the repo root:
#   pwsh scripts/demo.ps1
#   # or
#   .\scripts\demo.ps1

$ErrorActionPreference = 'Stop'

function Write-Section($title) {
    Write-Host ""
    Write-Host ("=" * 72) -ForegroundColor DarkGray
    Write-Host (" $title") -ForegroundColor White
    Write-Host ("=" * 72) -ForegroundColor DarkGray
}

# Resolve repo root (parent of scripts/) so the script works from anywhere.
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $repoRoot

Write-Section "ActionRail Finance"
Write-Host @"
Transaction runtime for finance AI agent actions.

ActionRail sits between finance AI agents and finance actions. Before an
agent approves, rejects, executes, or submits a risky finance action, ActionRail
creates a transaction and runs the checks finance teams require: vendor
verified, no duplicate, contract matches, amount within policy, evidence
attached, intent lock acquired. If a check fails the action is blocked or
routed for approval. If everything passes the action executes (in this MVP:
simulated only) and a tamper-evident HMAC-signed receipt is generated.
"@

Write-Section "Safety boundary"
Write-Host "Execution is simulated. No real money moves." -ForegroundColor Yellow
Write-Host "No bank, ERP, ledger writeback, or external finance API is called."

Write-Section "Step 1 / 4 — Run the test suite"
Write-Host "Running: pytest -q" -ForegroundColor Cyan
pytest -q
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Tests failed. Stop here, fix them, then re-run this script." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Section "Step 2 / 4 — Reset the demo database (manual)"
Write-Host "For a clean recording, run this in a fresh terminal:" -ForegroundColor Cyan
Write-Host ""
Write-Host "    python scripts/reset_demo_db.py" -ForegroundColor White
Write-Host ""
Write-Host "It drops and re-seeds only the local SQLite file (actionrail.db)."
Write-Host "It never touches external systems."
Write-Host "If uvicorn is running, stop it first."

Write-Section "Step 3 / 4 — Start the server (manual)"
Write-Host "Run this and leave it running:" -ForegroundColor Cyan
Write-Host ""
Write-Host "    uvicorn app.main:app --reload" -ForegroundColor White

Write-Section "Step 4 / 4 — Open these URLs"
Write-Host ""
Write-Host "    Dashboard: http://127.0.0.1:8000/dashboard" -ForegroundColor White
Write-Host "    Swagger:   http://127.0.0.1:8000/docs"
Write-Host "    Manifest:  http://127.0.0.1:8000/actionrail/manifest.json"
Write-Host "    Health:    http://127.0.0.1:8000/health"

Write-Section "Browser demo flow"
Write-Host @"
1.  Reset the demo DB (Step 2 above) for a clean slate.
2.  Start uvicorn (Step 3 above).
3.  Open the dashboard.
4.  Click "Approval Required Invoice".
5.  Review the transaction detail page.
6.  Click "Approve".
7.  Click "Execute".
8.  Click "View Receipt" to see the signed HMAC-SHA256 receipt.
9.  Return to the dashboard.
10. Click "Duplicate Invoice"   - confirm it lands as BLOCKED.
11. Click "Missing Evidence Invoice" - confirm it lands as NEEDS MORE EVIDENCE.
"@

Write-Section "Done"
Write-Host "Tests passed. Follow the manual steps above to record the demo." -ForegroundColor Green

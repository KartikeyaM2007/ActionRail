# Handoff
 
**Current Project State**: MVP is complete, fully prepared for public demo. 16 of 17 demo screenshots captured and embedded in `WorkFlow.md`.
**What Changed**: Captured 16 real screenshots using automated Selenium + Edge headless into `docs/demo_captures/`. Updated `WorkFlow.md` with screenshot status table and embedded image links. Updated `README.md` with live demo workflow pointer. Updated `docs/screenshots/README.md`.
**How to Run**: `uvicorn app.main:app --reload`
**Important Files Touched**: `WorkFlow.md`, `README.md`, `docs/screenshots/README.md`, `docs/demo_captures/*.png`, `scripts/capture_demo_screenshots.py`, `TASKS.md`, `CHANGELOG.md`, `ForKnow.md`, `HANDOFF.md`.
**What to do Next**: Optionally capture `01-preflight-response.png` manually from a terminal screenshot. Optionally record a demo video using OBS or Xbox Game Bar.
**Known Issues**: `01-preflight-response.png` is pending manual capture (terminal/API output, not a web page). All other screenshots captured.
**What not to change**: No real external database/ledger/payment connections should be added. Maintain "simulated-only" status. Do not change JSON API response shapes or receipt signature payloads.

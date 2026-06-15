# Handoff
 
**Current Project State**: MVP is complete and ready for live deployment. Configured for Render.com and Docker to preserve the local SQLite DB and filesystem seamlessly.
**What Changed**: Added `render.yaml`, `Dockerfile`, `.env.example`, `.dockerignore`, `docs/DEPLOYMENT.md`. Updated `app/store.py` and `app/main.py` to respect environment variables for file paths without breaking local development.
**How to Run (Local)**: `uvicorn app.main:app --reload`
**How to Run (Docker)**: `docker build -t actionrail-finance . && docker run -d -p 8000:8000 actionrail-finance`
**Important Files Touched**: `app/store.py`, `app/main.py`, `render.yaml`, `Dockerfile`, `docs/DEPLOYMENT.md`, `CHANGELOG.md`, `ForKnow.md`, `HANDOFF.md`.
**What to do Next**: Choose a hosting provider (Render.com recommended) and push the code. Provide the `ACTIONRAIL_SESSION_SECRET` environment variable in the dashboard.
**Known Issues**: None. The MVP is ready.
**What not to change**: No real external database/ledger/payment connections should be added. Maintain "simulated-only" status.

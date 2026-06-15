# Deployment Guide

ActionRail Finance is built as a self-contained MVP using a local SQLite database (`actionrail.db`) and local filesystem storage for uploaded evidence (`data/uploads/`).

To deploy this live safely without losing data on every restart, you must use a host that supports **persistent volumes**. Standard ephemeral hosts (like Heroku free tier, basic Google Cloud Run, Vercel) will wipe your database.

## Recommended: Render.com (PaaS)

Render provides the easiest "push to deploy" experience that supports persistent disks.

1. Fork this repository or connect your GitHub account to Render.
2. In Render, create a new **Web Service**.
3. Render should automatically detect the `render.yaml` configuration in the root directory.
4. During setup, Render will create a persistent disk mounted at `/data`.
5. Your SQLite database and uploaded files will be stored safely on this disk.

### Environment Variables
Render will prompt you or you can manually add these in the Render dashboard:
- `ACTIONRAIL_SESSION_SECRET`: Set to a strong random string (e.g., generate with `openssl rand -hex 32`).

## Alternative: Docker & VPS (AWS EC2, DigitalOcean, Fly.io)

We provide a standard `Dockerfile` and `.dockerignore`.

1. **Build the image**:
   ```bash
   docker build -t actionrail-finance .
   ```
2. **Run the container** (mounting a local folder `~/actionrail-data` to `/data`):
   ```bash
   docker run -d -p 8000:8000 \
     -v ~/actionrail-data:/data \
     -e ACTIONRAIL_SESSION_SECRET=your-secret \
     actionrail-finance
   ```

## Authentication Note

The MVP seeds a default local database with demo user accounts (e.g., `admin@example.local` / `admin123`). 

**WARNING**: If you deploy this publicly, anyone reading these docs can log into your instance. To secure your instance:
1. Log in immediately as admin.
2. Go to the database directly or build a user management CLI command to change the admin password.
3. Or, edit `app/auth.py` and `app/store.py` before deploying to change the default seeded password hash.

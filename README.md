# Asset Tracker Web Application

Production-ready Asset Tracking System with FastAPI + Vanilla JS frontend.

## Features

- JWT authentication with bcrypt hashing
- Role-based access control (`admin`, `viewer`)
- Employee, asset, assignment management
- One-shot onboarding/offboarding from dashboard
- Reports and CSV/Excel export
- Excel import for employees/assets
- PostgreSQL (Neon recommended), SQLite fallback for local development
- Backup and restore APIs with checksum validation

## Local Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
uvicorn backend.main:app --reload
```

Open:

- App: `http://127.0.0.1:8000/`
- API docs: `http://127.0.0.1:8000/docs`

## Neon PostgreSQL (Recommended)

1. Create a Neon project and database.
2. Copy Neon SQLAlchemy URL (psycopg2) format, for example:
   - `postgresql+psycopg2://USER:PASSWORD@HOST/DB?sslmode=require`
3. Set `DATABASE_URL` to that value.

If `DATABASE_URL` is set, the app uses it directly (on Render and local).

## Render Deployment with Neon

This repo includes `render.yaml` for Render Blueprint.

1. Push to GitHub.
2. In Render: `New` -> `Blueprint`.
3. Connect repo and deploy.
4. In Render service environment variables, set:
   - `DATABASE_URL` = your Neon connection URL

The web service runs:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

## Default Users (Auto-Seeded)

On first startup (if not already present):

- Admin: `admin@company.com` / `Admin@123`
- Viewer users: `ceo@company.com`, `hr@company.com`, `accounts@company.com`
- Viewer password: `Viewer@123`

Change these immediately in production.

## Backup and Recovery (Expert Mode)

Admin-only backup endpoints:

- `GET /api/backups/summary` -> row counts per table
- `GET /api/backups/export` -> full ZIP backup (`backup.json` + checksum manifest)
- `POST /api/backups/snapshot` -> writes ZIP snapshot to `BACKUP_DIR`, prunes old files by retention
- `POST /api/backups/restore?mode=replace|merge` -> restore from uploaded ZIP backup

### Recommended backup strategy

1. Schedule regular `GET /api/backups/export` from a secure automation job.
2. Store ZIP files in durable object storage (S3/Backblaze/GCS).
3. Keep multiple restore points (daily + weekly retention).
4. Test `restore?mode=merge` in staging every month.

## Environment Variables

See `.env.example` for full list. Key ones:

- `DATABASE_URL`
- `SECRET_KEY`
- `CORS_ORIGINS`
- `DEFAULT_ADMIN_*`
- `DEFAULT_VIEWER_*`
- `BACKUP_DIR`
- `BACKUP_RETENTION_DAYS`

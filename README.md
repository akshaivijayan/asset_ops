# Asset Tracker Web Application

Production-ready Asset Tracking System that replaces manual Excel-based tracking.

## Features

- JWT authentication with bcrypt password hashing
- Role-based access control (`admin`, `viewer`)
- Employee management (CRUD + deactivate/offboard)
- Asset management (CRUD + status tracking)
- Asset assignments and return workflow with history
- Dashboard statistics and recent assignments
- Reports:
  - Assets by employee
  - Unassigned assets
  - Assets under repair
  - Warranty expiring soon
- Export reports to CSV or Excel
- Import employees/assets from Excel
- PostgreSQL-ready with SQLite fallback in development
- Soft delete behavior for employee/asset records

## Tech Stack

- Frontend: HTML, CSS, Vanilla JavaScript
- Backend: FastAPI (Python)
- ORM: SQLAlchemy
- Database: PostgreSQL (preferred), SQLite fallback
- Auth: JWT (`python-jose`) + `bcrypt`

## Setup (Local)

1. Create virtual environment and install dependencies:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

2. Configure environment:

```bash
copy .env.example .env
```

3. Run app:

```bash
uvicorn backend.main:app --reload
```

4. Open app:

- `http://127.0.0.1:8000/` (frontend + API)
- `http://127.0.0.1:8000/docs` (Swagger)

## Database Configuration

### SQLite (Development)

Default in `APP_ENV=development` when `DATABASE_URL` is empty.

### PostgreSQL (Preferred)

Set either:

- `DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname`

or set individual `POSTGRES_*` vars.

Tables are auto-created on startup.

## Default Users (Auto-Seeded)

Created automatically at startup if they do not exist:

- Admin:
  - Email: `admin@company.com`
  - Password: `Admin@123`
- Viewer users:
  - Emails: `ceo@company.com`, `hr@company.com`, `accounts@company.com`
  - Password: `Viewer@123`

Change these in `.env` for production.

## Render Deployment (Web + PostgreSQL)

This repo includes `render.yaml` for Blueprint deployment.

1. Push code to GitHub.
2. In Render: `New` -> `Blueprint`.
3. Connect this repository and select branch `main`.
4. Render will create:
   - `asset-ops-web` (FastAPI service)
   - `asset-ops-db` (PostgreSQL)

The app starts with:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

`DATABASE_URL` is automatically wired from the Render PostgreSQL service.

## API Endpoints

- `POST /api/auth/login`
- `POST /api/auth/users` (admin)
- `GET|POST|PUT|DELETE /api/employees`
- `POST /api/employees/onboard` (admin)
- `POST /api/employees/offboard` (admin)
- `GET|POST|PUT|DELETE /api/assets`
- `GET|POST|PUT /api/assignments`
- `GET /api/reports/*`
- `GET /api/reports/export/{report_name}?fmt=csv|excel`
- `POST /api/reports/import/employees`
- `POST /api/reports/import/assets`

## Excel Import Format

### Employees.xlsx columns

- `name`, `email`, `phone`, `designation`, `department`, `reporting_person`, `office_location`, `joining_date`, `employment_status`, `notes`

### Assets.xlsx columns

- `asset_unique_id`, `asset_name`, `category`, `brand`, `model`, `serial_number`, `purchase_date`, `purchase_cost`, `vendor`, `warranty_expiry`, `asset_location`, `status`

## Production Notes

- Set secure `SECRET_KEY`
- Restrict `CORS_ORIGINS`
- Use PostgreSQL
- Rotate default credentials after first deployment
- Use HTTPS

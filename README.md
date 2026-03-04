# Asset Tracker Web Application

Production-ready Asset Tracking System for Real Estate company IT operations, replacing manual Excel-based tracking.

## Features

- JWT authentication with bcrypt password hashing
- Role-based access control (`admin`, `viewer`)
- Employee management (CRUD + deactivate)
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
- Auth: JWT (`python-jose`) + `passlib[bcrypt]`

## Project Structure

```text
asset-tracker
¦
+-- backend
¦   +-- main.py
¦   +-- database.py
¦   +-- models.py
¦   +-- schemas.py
¦   +-- auth.py
¦   +-- config.py
¦   +-- routers
¦   ¦   +-- auth.py
¦   ¦   +-- employees.py
¦   ¦   +-- assets.py
¦   ¦   +-- assignments.py
¦   ¦   +-- reports.py
¦   +-- utils
¦       +-- security.py
¦       +-- excel_import.py
¦
+-- frontend
¦   +-- index.html
¦   +-- dashboard.html
¦   +-- employees.html
¦   +-- assets.html
¦   +-- assignments.html
¦   +-- reports.html
¦   +-- css
¦   ¦   +-- styles.css
¦   +-- js
¦       +-- api.js
¦       +-- auth.js
¦       +-- employees.js
¦       +-- assets.js
¦       +-- assignments.js
¦       +-- reports.js
¦       +-- dashboard.js
¦
+-- requirements.txt
+-- .env.example
+-- README.md
```

## Setup Instructions

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
- Swagger API docs: `http://127.0.0.1:8000/docs`

## Database Configuration

### SQLite (Development)

Default in `APP_ENV=development` when `DATABASE_URL` is empty.

### PostgreSQL (Preferred)

Set either:

- `DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname`

or set individual `POSTGRES_*` vars and switch `APP_ENV` from `development` if desired.

Tables are auto-created on startup.

## Default Login

Created automatically at startup if not present:

- Email: `admin@company.com`
- Password: `Admin@123`

Change these in `.env` for production.

## RBAC

- `admin` (IT Admin): full create/update/delete/import/export actions.
- `viewer` (CEO/HR/Accounts): read-only access to dashboards, employees, assets, assignments, reports.

## API Endpoints

- `POST /api/auth/login`
- `POST /api/auth/users` (admin)
- `GET|POST|PUT|DELETE /api/employees`
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
- Rotate default admin credentials
- Run behind reverse proxy (Nginx/Traefik)
- Use HTTPS

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, SessionLocal, engine
from .models import User
from .routers import assets, assignments, auth, backups, employees, reports
from .utils.security import hash_password

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == settings.DEFAULT_ADMIN_EMAIL).first()
        if not admin:
            db.add(
                User(
                    name=settings.DEFAULT_ADMIN_NAME,
                    email=settings.DEFAULT_ADMIN_EMAIL,
                    password_hash=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                    role="admin",
                )
            )
            db.flush()

        # Seed default viewer users for CEO/HR/Accounts access.
        viewer_emails = [email.strip().lower() for email in settings.DEFAULT_VIEWER_EMAILS.split(",") if email.strip()]
        for email in viewer_emails:
            exists = db.query(User).filter(User.email == email).first()
            if exists:
                continue
            name = email.split("@")[0].replace(".", " ").replace("_", " ").title()
            db.add(
                User(
                    name=name or "Viewer User",
                    email=email,
                    password_hash=hash_password(settings.DEFAULT_VIEWER_PASSWORD),
                    role="viewer",
                )
            )
        db.commit()
    finally:
        db.close()


app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(assets.router)
app.include_router(assignments.router)
app.include_router(reports.router)
app.include_router(backups.router)

frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

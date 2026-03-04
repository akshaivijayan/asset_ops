from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings


def build_database_url() -> str:
    db_url = settings.resolved_database_url
    if settings.APP_ENV == "development" and not settings.DATABASE_URL:
        # Fallback to SQLite when Postgres is not explicitly configured.
        db_url = f"sqlite:///{settings.SQLITE_DB_PATH}"
    return db_url


DATABASE_URL = build_database_url()
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

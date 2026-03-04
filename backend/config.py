import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Asset Tracker")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "asset_tracker")

    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "./asset_tracker.db")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")

    DEFAULT_ADMIN_NAME: str = os.getenv("DEFAULT_ADMIN_NAME", "IT Admin")
    DEFAULT_ADMIN_EMAIL: str = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@company.com")
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin@123")
    DEFAULT_VIEWER_EMAILS: str = os.getenv("DEFAULT_VIEWER_EMAILS", "ceo@company.com,hr@company.com,accounts@company.com")
    DEFAULT_VIEWER_PASSWORD: str = os.getenv("DEFAULT_VIEWER_PASSWORD", "Viewer@123")
    BACKUP_DIR: str = os.getenv("BACKUP_DIR", "./backups")
    BACKUP_RETENTION_DAYS: int = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))

    @property
    def resolved_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()

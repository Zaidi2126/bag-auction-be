import os
from datetime import datetime
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


# Hardcoded for Vercel / no .env (change or use .env to override)
GMAIL_APP_PASSWORD = "qnnqybyclpdbbsvr"
HARDCODED_SMTP_USER = "shehroz.i.zaidi@gmail.com"
HARDCODED_CORS_ORIGINS = "https://bag-auction-fe.vercel.app,https://auction-fe.vercel.app,http://localhost:5173,http://localhost:3000"


def _default_database_url() -> str:
    if os.environ.get("VERCEL"):
        return "sqlite:////tmp/auction.db"
    return "sqlite:///./auction.db"


class Settings(BaseSettings):
    database_url: str = Field(default_factory=_default_database_url)
    secret_key: str = "dev-secret-change-in-production"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = HARDCODED_SMTP_USER
    smtp_password: Optional[str] = GMAIL_APP_PASSWORD
    smtp_from: Optional[str] = None
    auction_start_time: Optional[str] = None  # ISO format
    cors_origins: Optional[str] = HARDCODED_CORS_ORIGINS

    @property
    def smtp_configured(self) -> bool:
        return bool(self.smtp_user and (self.smtp_password or GMAIL_APP_PASSWORD))

    def get_smtp_password(self) -> str:
        return self.smtp_password or GMAIL_APP_PASSWORD

    def get_auction_start_time(self) -> datetime:
        if self.auction_start_time:
            try:
                return datetime.fromisoformat(
                    self.auction_start_time.replace("Z", "+00:00")
                )
            except ValueError:
                pass
        return datetime.utcnow()

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

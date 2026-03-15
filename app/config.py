import os
from datetime import datetime
from typing import Optional

from pydantic_settings import BaseSettings


# Gmail app password (hardcoded for now). Set SMTP_USER in .env to your Gmail address.
GMAIL_APP_PASSWORD = "qnnqybyclpdbbsvr"


class Settings(BaseSettings):
    database_url: str = "sqlite:///./auction.db"
    secret_key: str = "dev-secret-change-in-production"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None  # defaults to GMAIL_APP_PASSWORD if unset
    smtp_from: Optional[str] = None
    auction_start_time: Optional[str] = None  # ISO format

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

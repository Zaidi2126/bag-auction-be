import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models import OTPCode, Session as SessionModel, User


OTP_EXPIRY_MINUTES = 5
SESSION_DAYS = 7


def generate_otp() -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(6))


def create_otp(db: Session, email: str) -> str:
    code = generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)
    otp_row = OTPCode(email=email, code=code, expires_at=expires_at)
    db.add(otp_row)
    db.commit()
    return code


def get_valid_otp(db: Session, email: str, code: str) -> Optional[OTPCode]:
    now = datetime.now(timezone.utc)
    row = (
        db.query(OTPCode)
        .filter(
            OTPCode.email == email,
            OTPCode.code == code,
            OTPCode.used == False,
            OTPCode.expires_at > now,
        )
        .first()
    )
    return row


def mark_otp_used(db: Session, otp_row: OTPCode) -> None:
    otp_row.used = True
    db.commit()


def get_or_create_user(db: Session, email: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def create_session_token(db: Session, user_id: int, secret_key: str) -> str:
    raw = f"{user_id}:{secrets.token_hex(32)}"
    token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    session = SessionModel(user_id=user_id, token=token, expires_at=expires_at)
    db.add(session)
    db.commit()
    return token


def get_user_by_token(db: Session, token: str) -> Optional[User]:
    if not token:
        return None
    now = datetime.now(timezone.utc)
    session = (
        db.query(SessionModel)
        .filter(SessionModel.token == token, SessionModel.expires_at > now)
        .first()
    )
    if session is None:
        return None
    return db.query(User).filter(User.id == session.user_id).first()

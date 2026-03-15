import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import (
    create_otp,
    create_session_token,
    get_or_create_user,
    get_valid_otp,
    mark_otp_used,
)
from app.config import settings
from app.database import get_db
from app.email_otp import send_otp_email
from app.schemas import RequestOTPIn, UserOut, VerifyOTPIn, VerifyOTPOut

router = APIRouter(prefix="/auth", tags=["auth"])
log = logging.getLogger("auction")


@router.post("/request_otp")
def request_otp(body: RequestOTPIn, db: Session = Depends(get_db)):
    log.info("Request OTP for email: %s", body.email)
    code = create_otp(db, body.email)
    sent = send_otp_email(body.email, code)
    if not sent and settings.smtp_configured:
        log.error("OTP email failed for %s", body.email)
        raise HTTPException(
            status_code=500,
            detail="Failed to send OTP email.",
        )
    out = {"message": "OTP sent. Check your email."}
    if not settings.smtp_configured:
        out["otp"] = code
        out["message"] = "OTP generated. (SMTP not configured — use the code below to sign in.)"
    return out


@router.post("/verify_otp", response_model=VerifyOTPOut)
def verify_otp(body: VerifyOTPIn, db: Session = Depends(get_db)):
    otp_row = get_valid_otp(db, body.email, body.otp)
    if otp_row is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OTP.",
        )
    mark_otp_used(db, otp_row)
    user = get_or_create_user(db, body.email)
    token = create_session_token(db, user.id, settings.secret_key)
    return VerifyOTPOut(token=token, user=UserOut.model_validate(user))

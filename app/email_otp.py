import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings

log = logging.getLogger("auction")


def _otp_html_body(code: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your auction code</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center;">
  <div style="max-width: 420px; width: 100%; margin: 24px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.4); border-radius: 20px; overflow: hidden; background: #ffffff;">
    <div style="background: linear-gradient(135deg, #e94560 0%, #c23a51 100%); padding: 32px 24px; text-align: center;">
      <h1 style="margin: 0; font-size: 22px; font-weight: 700; color: #fff; letter-spacing: -0.5px;">Bag Auction</h1>
      <p style="margin: 8px 0 0; font-size: 14px; color: rgba(255,255,255,0.9);">Your one-time code</p>
    </div>
    <div style="padding: 36px 28px;">
      <p style="margin: 0 0 20px; font-size: 15px; color: #374151; line-height: 1.5;">Use this code to sign in or register. It expires in <strong>5 minutes</strong>.</p>
      <div style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border: 2px dashed #e94560; border-radius: 14px; padding: 24px; text-align: center;">
        <span style="font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #1a1a2e; font-variant-numeric: tabular-nums;">{code}</span>
      </div>
      <p style="margin: 24px 0 0; font-size: 13px; color: #6b7280; text-align: center;">Do not share this code with anyone.</p>
    </div>
    <div style="padding: 0 28px 28px;">
      <p style="margin: 0; font-size: 12px; color: #9ca3af; text-align: center;">The Legendary Black Pouch Bag · Friends-only auction</p>
    </div>
  </div>
</body>
</html>
"""


def _otp_plain_body(code: str) -> str:
    return f"Your one-time code is: {code}\n\nIt expires in 5 minutes. Do not share it.\n\n— Bag Auction"


def send_otp_email(to_email: str, code: str) -> bool:
    if not settings.smtp_configured:
        log.warning("OTP for %s (no SMTP): code = %s — include in API response for user", to_email, code)
        return True

    log.info("Sending OTP email to %s (code: %s)", to_email, code)
    subject = "Your auction code — Bag Auction"
    html = _otp_html_body(code)
    plain = _otp_plain_body(code)

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.get_smtp_password())
            server.sendmail(msg["From"], to_email, msg.as_string())
        log.info("OTP email sent to %s", to_email)
        return True
    except Exception as e:
        log.exception("Failed to send OTP email to %s: %s", to_email, e)
        return False

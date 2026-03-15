import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings


def send_otp_email(to_email: str, code: str) -> bool:
    if not settings.smtp_configured:
        print(f"[OTP] Email: {to_email} | Code: {code}")
        return True

    subject = "Your auction OTP code"
    body = f"Your one-time code is: {code}\n\nIt expires in 5 minutes. Do not share it."

    msg = MIMEMultipart()
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        port = settings.smtp_port or 587
        with smtplib.SMTP(settings.smtp_host, port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(msg["From"], to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[OTP] Failed to send email: {e}")
        return False

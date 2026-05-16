import os
from pathlib import Path
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from fastapi_mail.errors import ConnectionErrors
from jose import jwt
from auth import SECRET_KEY, ALGORITHM

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_FROM_NAME="Contacts Management System",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

async def send_verification_email(email: str, username: str, host: str):
    """
    Generates a token and sends a verification email.
    """
    try:
        token_data = {"sub": email}
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        base_host = host.rstrip('/')
        confirmation_url = f"{base_host}/auth/confirm/{token}"
        
        message = MessageSchema(
            subject="Please confirm your email",
            recipients=[email],
            body=f"Hello {username},<br>Please confirm your email by clicking the link: <a href='{confirmation_url}'>Confirm Email</a>",
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        print(f"DEBUG: Attempting to send email to {email} via server {os.getenv('MAIL_SERVER')}...", flush=True)
        await fm.send_message(message)
        print("DEBUG: Email sent successfully!", flush=True)
        
    except ConnectionErrors as e:
        print(f"CRITICAL: Email connection error: {e}", flush=True)
    except Exception as e:
        # 🌟 ГОЛОВНЕ ВИПРАВЛЕННЯ: ловимо абсолютно всі помилки і примусово виводимо в логи
        print(f"CRITICAL: Unexpected email error type {type(e)}: {e}", flush=True)

async def send_reset_password_email(email: str, username: str, host: str):
    """
    Генерує токен та відправляє email для скидання пароля.
    """
    try:
        token_data = {"sub": email, "action": "reset_password"}
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        base_host = host.rstrip('/')
        reset_url = f"{base_host}/auth/reset-password/{token}"
        
        message = MessageSchema(
            subject="Password Reset Request",
            recipients=[email],
            body=f"Hello {username},<br>You requested a password reset. Click the link to set a new password: <a href='{reset_url}'>Reset Password</a>",
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message)
    except ConnectionErrors as e:
        print(f"Email connection error: {e}")
import os
from pathlib import Path
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from fastapi_mail.errors import ConnectionErrors
from jose import jwt
from auth import SECRET_KEY, ALGORITHM, create_reset_password_token

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 465)),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_FROM_NAME="Contacts Management System",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

async def send_verification_email(email: str, username: str, host: str):
    """
    Generates a unique verification token and dispatches a confirmation email to the user.

    :param email: The recipient's email address.
    :type email: str
    :param username: The username used for personalizing the email greeting.
    :type username: str
    :param host: The base URL of the application host used to build the verification link.
    :type host: str
    :return: None
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
        await fm.send_message(message)
    except ConnectionErrors as e:
        print(f"Email connection error: {e}")

async def send_reset_password_email(email: str, username: str, host: str):
    """
    Generates a token with a 15-minute lifespan and sends a password reset email.
    """
    try:
        token = create_reset_password_token(email)
        
        base_host = host.rstrip('/')
        reset_url = f"{base_host}/auth/reset-password?token={token}"
        
        message = MessageSchema(
            subject="Password Reset Request",
            recipients=[email],
            body=f"Hello {username},<br>You requested a password reset. Click the link to set a new password: <a href='{reset_url}'>Reset Password</a><br>This link is valid for 15 minutes.",
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message)
    except ConnectionErrors as e:
        print(f"Email connection error: {e}")
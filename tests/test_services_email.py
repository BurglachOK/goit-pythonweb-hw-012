import pytest
from unittest.mock import AsyncMock, patch
from fastapi_mail.errors import ConnectionErrors
from services.email import send_verification_email, send_reset_password_email

@pytest.mark.asyncio
@patch("services.email.FastMail.send_message", new_callable=AsyncMock)
async def test_send_verification_email_success(mock_send_message):
    await send_verification_email(
        email="testuser@example.com",
        username="testuser",
        host="http://localhost:8000"
    )
    mock_send_message.assert_called_once()


@pytest.mark.asyncio
@patch("services.email.FastMail.send_message", new_callable=AsyncMock)
async def test_send_reset_password_email_success(mock_send_message):
    await send_reset_password_email(
        email="testuser@example.com",
        username="testuser",
        host="http://localhost:8000"
    )
    mock_send_message.assert_called_once()


@pytest.mark.asyncio
@patch("services.email.FastMail.send_message")
async def test_send_email_connection_error(mock_send_message):
    mock_send_message.side_effect = ConnectionErrors(Exception("SMTP error"))
    
    await send_verification_email(
        email="testuser@example.com",
        username="testuser",
        host="http://localhost:8000"
    )
    
    await send_reset_password_email(
        email="testuser@example.com",
        username="testuser",
        host="http://localhost:8000"
    )
    
    assert mock_send_message.call_count == 2
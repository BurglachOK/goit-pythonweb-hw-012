import pytest
from unittest.mock import AsyncMock
from jose import jwt
from auth import SECRET_KEY, ALGORITHM, get_password_hash
import models

@pytest.fixture(autouse=True)
def mock_email_services(monkeypatch):
    monkeypatch.setattr("main.send_verification_email", AsyncMock())
    monkeypatch.setattr("main.send_reset_password_email", AsyncMock())

@pytest.fixture
def test_user(db_session):
    user = db_session.query(models.User).filter(models.User.email == "endpoint_tester@example.com").first()
    if not user:
        user = models.User(
            email="endpoint_tester@example.com",
            username="endpoint_tester",
            password=get_password_hash("supersecurepassword"),
            confirmed=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


def test_register_duplicate_email(client, test_user):
    response = client.post(
        "/auth/register", 
        json={"email": "endpoint_tester@example.com", "username": "user2", "password": "password123"}
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"

def test_login_invalid_password(client, test_user):
    response = client.post(
        "/auth/login", 
        data={"username": "endpoint_tester@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_request_email_reset_password(client, test_user):
    response = client.post("/auth/request-password-reset", json={"email": "endpoint_tester@example.com"})
    
    assert response.status_code == 200
    assert response.json()["message"] == "Password reset link sent to your email."

def test_confirm_email_invalid_token(client):
    response = client.get("/auth/confirm/invalid.token.here")
    assert response.status_code == 400
    assert response.json()["detail"] == "Token is invalid or expired"

def test_confirm_email_success(client, db_session, test_user):
    token = jwt.encode({"sub": "endpoint_tester@example.com"}, SECRET_KEY, algorithm=ALGORITHM)
    
    test_user.confirmed = False
    db_session.commit()

    response = client.get(f"/auth/confirm/{token}")
    assert response.status_code == 200
    assert response.json()["message"] == "Email confirmed successfully"

def test_request_password_reset_user_not_found(client):
    response = client.post("/auth/request-password-reset", json={"email": "ghost_user@example.com"})
    assert response.status_code == 200
    assert response.json()["message"] == "If the email exists, a reset link has been sent."


@pytest.fixture
def auth_headers(client, db_session, test_user):
    test_user.confirmed = True
    db_session.commit()

    login_response = client.post(
        "/auth/login", 
        data={"username": "endpoint_tester@example.com", "password": "supersecurepassword"}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_get_contact_not_found(client, auth_headers):
    response = client.get("/contacts/9999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Contact not found"

def test_update_contact_not_found(client, auth_headers):
    response = client.patch(
        "/contacts/9999", 
        json={"first_name": "Ghost", "last_name": "Ghost", "email": "ghost@example.com"}, 
        headers=auth_headers
    )
    assert response.status_code == 404

def test_delete_contact_not_found(client, auth_headers):
    response = client.delete("/contacts/9999", headers=auth_headers)
    assert response.status_code == 404

def test_read_users_me(client, auth_headers):
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "endpoint_tester@example.com"
    
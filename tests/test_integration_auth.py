import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
import models
import auth
from auth import RoleChecker, get_current_user, get_password_hash


@pytest.fixture(autouse=True)
def mock_email_services(monkeypatch):
    """
    Automatically stops sending emails for all tests in this file,
    to avoid connection errors to SMTP.
    """
    monkeypatch.setattr("main.send_verification_email", AsyncMock())
    monkeypatch.setattr("main.send_reset_password_email", AsyncMock())


def test_auth_and_contacts_workflow(client, db_session):
    """
    Complex integration test for the standard user flow:
    Registration -> Blocking until login -> Confirmation -> Login -> Contact Operations.
    """
    reg_response = client.post(
        "/auth/register",
        json={"email": "tester@example.com", "username": "tester", "password": "supersecurepassword"}
    )
    assert reg_response.status_code == 201
    assert reg_response.json()["email"] == "tester@example.com"
    assert reg_response.json()["role"] == "user"

    login_fail = client.post(
        "/auth/login",
        data={"username": "tester@example.com", "password": "supersecurepassword"}
    )
    assert login_fail.status_code == 401

    user = db_session.query(models.User).filter(models.User.email == "tester@example.com").first()
    assert user is not None
    user.confirmed = True
    db_session.commit()

    login_success = client.post(
        "/auth/login",
        data={"username": "tester@example.com", "password": "supersecurepassword"}
    )
    assert login_success.status_code == 200
    token = login_success.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    contact_response = client.post(
        "/contacts/",
        json={
            "first_name": "Integration",
            "last_name": "Test",
            "email": "contact@example.com",
            "phone": "+380000000000",
            "birthday": "1995-05-15",
            "additional_data": "Created during integration testing"
        },
        headers=headers
    )
    assert contact_response.status_code == 201
    assert contact_response.json()["first_name"] == "Integration"


def test_register_admin_via_secret_token_success(client, db_session, monkeypatch):
    """
    Test checks the successful creation of an administrator through providing
    the correct ADMIN_REGISTRATION_TOKEN.
    """
    secret = "my_pytest_secret_token_2026"
    monkeypatch.setenv("ADMIN_REGISTRATION_TOKEN", secret)

    response = client.post(
        "/auth/register",
        json={
            "username": "superadmin",
            "email": "admin_test_success@example.com",
            "password": "securepassword123",
            "admin_token": secret
        }
    )

    assert response.status_code == 201
    assert response.json()["role"] == "admin"
    assert response.json()["email"] == "admin_test_success@example.com"

    user_db = db_session.query(models.User).filter(models.User.email == "admin_test_success@example.com").first()
    assert user_db is not None
    assert user_db.role == "admin"


def test_register_admin_via_secret_token_forbidden(client, db_session, monkeypatch):
    """
    Test checks that the system returns 403 Forbidden if an invalid admin registration token is provided.
    """
    monkeypatch.setenv("ADMIN_REGISTRATION_TOKEN", "real_secret_key")

    response = client.post(
        "/auth/register",
        json={
            "username": "fakeadmin",
            "email": "admin_test_fail@example.com",
            "password": "securepassword123",
            "admin_token": "wrong_and_malicious_token"
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid admin registration token"


@pytest.mark.asyncio
async def test_get_current_user_from_db_when_redis_fails(db_session, monkeypatch):
    """
    Checks the system's resilience: if Redis "fails" or is unavailable,
    get_current_user still retrieves the user from the relational database.
    """
    user = models.User(
        email="tester@example.com",
        username="tester",
        password=get_password_hash("supersecurepassword"),
        confirmed=True
    )
    db_session.query(models.User).filter(models.User.email == "tester@example.com").delete()
    db_session.add(user)
    db_session.commit()

    token = auth.create_access_token(data={"sub": "tester@example.com"})

    auth.redis_client.get.side_effect = Exception("Redis connection refused")

    current_user = await get_current_user(token=token, db=db_session)
    assert current_user.email == "tester@example.com"


@pytest.mark.asyncio
async def test_get_current_user_not_found_in_db(db_session):
    """
    Checks the generation of an exception if the token is decoded successfully,
    but the user with such an email is not found in the database.
    """
    fake_token = auth.create_access_token(data={"sub": "ghost_user@example.com"})
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=fake_token, db=db_session)
    assert exc_info.value.status_code in [400, 401]


def test_role_checker_forbidden_scenarios():
    """
    Checks the logic of RoleChecker on access restriction.
    """

    mock_user = MagicMock()
    mock_user.role = "user"
    
    admin_checker = RoleChecker(allowed_roles=["admin"])
    with pytest.raises(HTTPException) as exc_info:
        admin_checker(current_user=mock_user)
    assert exc_info.value.status_code == 403

    assert exc_info.value.detail == "You do not have permission to perform this action"

    mock_broken_user = MagicMock(spec=[]) 
    if hasattr(mock_broken_user, "role"):
        del mock_broken_user.role
    
    with pytest.raises(HTTPException) as exc_info_broken:
        admin_checker(current_user=mock_broken_user)
    assert exc_info_broken.value.status_code == 403
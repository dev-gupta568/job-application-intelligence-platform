from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from app.api.routes.auth import TOKEN_AUDIENCE, TOKEN_ISSUER
from app.core.config import get_settings


def test_registration_normalizes_email_and_login_is_case_insensitive(client):
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "Learner@Example.com",
            "display_name": "  Learner  ",
            "password": "a-long-test-password",
        },
    )
    assert registration.status_code == 201
    assert registration.json()["email"] == "learner@example.com"
    assert registration.json()["display_name"] == "Learner"
    assert "password" not in registration.json()
    assert "password_hash" not in registration.json()

    login = client.post(
        "/api/v1/auth/login",
        data={"username": " LEARNER@EXAMPLE.COM ", "password": "a-long-test-password"},
    )
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"


def test_duplicate_email_and_wrong_password_are_rejected(client, account):
    duplicate = client.post(
        "/api/v1/auth/register",
        json={
            "email": "LEARNER@example.com",
            "display_name": "Duplicate",
            "password": "a-different-long-password",
        },
    )
    assert duplicate.status_code == 409

    wrong_password = client.post(
        "/api/v1/auth/login",
        data={"username": "learner@example.com", "password": "wrong-password"},
    )
    unknown_email = client.post(
        "/api/v1/auth/login",
        data={"username": "unknown@example.com", "password": "wrong-password"},
    )
    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_me_route_returns_only_public_user_fields(client, account):
    response = client.get("/api/v1/auth/me", headers=account["headers"])
    assert response.status_code == 200
    assert response.json()["id"] == account["id"]
    assert "password_hash" not in response.json()


def test_password_is_stored_as_an_argon2_hash(client, account):
    from app.models.user import User

    with client.session_factory() as session:
        user = session.get(User, UUID(account["id"]))
        assert user.password_hash.startswith("$argon2id$")
        assert user.password_hash != "a-long-test-password"


def test_invalid_expired_and_inactive_user_tokens_are_rejected(client, account):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )
    assert response.status_code == 401

    settings = get_settings()
    secret = settings.jwt_secret_key.get_secret_value()
    expired_token = jwt.encode(
        {
            "sub": account["id"],
            "iat": datetime.now(timezone.utc) - timedelta(minutes=10),
            "nbf": datetime.now(timezone.utc) - timedelta(minutes=10),
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
            "iss": TOKEN_ISSUER,
            "aud": TOKEN_AUDIENCE,
        },
        secret,
        algorithm="HS256",
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401

    from app.models.user import User

    with client.session_factory() as session:
        user = session.get(User, UUID(account["id"]))
        user.is_active = False
        session.commit()

    response = client.get("/api/v1/auth/me", headers=account["headers"])
    assert response.status_code == 401

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "learner@example.com", "password": "a-long-test-password"},
    )
    assert response.status_code == 401


def test_token_with_wrong_issuer_is_rejected(client, account):
    secret = get_settings().jwt_secret_key.get_secret_value()
    token = jwt.encode(
        {
            "sub": account["id"],
            "iat": datetime.now(timezone.utc),
            "nbf": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
            "iss": "unexpected-issuer",
            "aud": TOKEN_AUDIENCE,
        },
        secret,
        algorithm="HS256",
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401

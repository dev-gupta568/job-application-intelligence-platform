import os
import asyncio

os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-only-secret-key-do-not-use-in-production-0123456789",
)
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.main import app
from app.models import Base


class SyncASGIClient:
    def __init__(self, application, session_factory):
        self.application = application
        self.session_factory = session_factory

    def request(self, method, url, **kwargs):
        async def send_request():
            transport = ASGITransport(app=self.application)
            async with AsyncClient(
                transport=transport,
                base_url="http://test",
            ) as client:
                return await client.request(method, url, **kwargs)

        return asyncio.run(send_request())

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)

    def patch(self, url, **kwargs):
        return self.request("PATCH", url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request("DELETE", url, **kwargs)

    def options(self, url, **kwargs):
        return self.request("OPTIONS", url, **kwargs)


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)

    def override_get_db():
        with TestingSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield SyncASGIClient(app, TestingSession)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def account(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "learner@example.com",
            "display_name": "Learner",
            "password": "a-long-test-password",
        },
    )
    assert response.status_code == 201
    assert "password_hash" not in response.json()
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "learner@example.com", "password": "a-long-test-password"},
    )
    assert login.status_code == 200
    return {
        "id": response.json()["id"],
        "headers": {"Authorization": f"Bearer {login.json()['access_token']}"},
    }

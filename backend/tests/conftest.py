from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def _build_test_session_factory():
    os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

    from app.database import Base
    from app.models import Dialect, Source, User
    from app.models.enums import Role, SourceType
    from app.security import get_password_hash

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        db.add_all(
            [
                User(
                    email="user@example.com",
                    display_name="User",
                    password_hash=get_password_hash("ChangeMe123!"),
                    role=Role.user,
                ),
                User(
                    email="reviewer@example.com",
                    display_name="Reviewer",
                    password_hash=get_password_hash("ChangeMe123!"),
                    role=Role.reviewer,
                ),
                User(
                    email="admin@example.com",
                    display_name="Admin",
                    password_hash=get_password_hash("ChangeMe123!"),
                    role=Role.admin,
                ),
                Dialect(code="sahidic", name="Sahidic"),
                Source(title="Seed Lexicon", type=SourceType.lexicon),
            ]
        )
        db.commit()

    return TestingSessionLocal


@pytest.fixture(autouse=True)
def reset_rate_limiters() -> None:
    from app.services.rate_limit import login_rate_limiter, translate_rate_limiter
    login_rate_limiter.reset()
    translate_rate_limiter.reset()


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    TestingSessionLocal = _build_test_session_factory()
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    from app.database import get_db
    from app.main import app

    TestingSessionLocal = _build_test_session_factory()

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def auth_header(client: TestClient, email: str, password: str = "ChangeMe123!") -> dict[str, str]:
    if password == "secret":
        password = "ChangeMe123!"
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


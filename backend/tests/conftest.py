import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import User, Category, Tag
from backend.app.utils.security import hash_password, create_access_token

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    admin_user = User(
        id=1,
        name="Admin Tester",
        email="admin@test.com",
        password_hash=hash_password("Password123!"),
        role="admin",
        is_active=True,
    )
    user_one = User(
        id=2,
        name="User One",
        email="user1@test.com",
        password_hash=hash_password("Password123!"),
        role="user",
        is_active=True,
    )
    user_two = User(
        id=3,
        name="User Two",
        email="user2@test.com",
        password_hash=hash_password("Password123!"),
        role="user",
        is_active=True,
    )
    session.add_all([admin_user, user_one, user_two])
    session.flush()

    cat = Category(id=1, name="Technology", slug="technology", description="Tech articles")
    session.add(cat)
    tag1 = Tag(id=1, name="Python", slug="python")
    tag2 = Tag(id=2, name="FastAPI", slug="fastapi")
    session.add_all([tag1, tag2])

    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_headers():
    token = create_access_token(subject="1")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_headers():
    token = create_access_token(subject="2")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user2_headers():
    token = create_access_token(subject="3")
    return {"Authorization": f"Bearer {token}"}

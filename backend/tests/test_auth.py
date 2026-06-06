"""
Auth endpoint testleri.
Gerçek bir PostgreSQL yerine test içinde override edilen bağımlılıklar kullanılır.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.database import get_db
from app.models import Base
from app.core.security import hash_password
from app.models.user import User

# --- Test veritabanı (bellek içi SQLite) ---
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# --- Tests ---

@pytest.mark.anyio
async def test_register_success(client: AsyncClient):
    payload = {
        "email": "test@example.com",
        "password": "strongpass123",
        "full_name": "Test User",
        "user_type": "individual",
    }
    resp = await client.post("/v1/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["full_name"] == "Test User"


@pytest.mark.anyio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {
        "email": "dup@example.com",
        "password": "strongpass123",
        "full_name": "Dup User",
    }
    resp1 = await client.post("/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = await client.post("/v1/auth/register", json=payload)
    assert resp2.status_code == 409


@pytest.mark.anyio
async def test_login_success(client: AsyncClient, db_session: AsyncSession):
    # Önce kullanıcı oluştur
    user = User(
        email="login@example.com",
        password_hash=hash_password("correctpass"),
        full_name="Login User",
    )
    db_session.add(user)
    await db_session.commit()

    payload = {"email": "login@example.com", "password": "correctpass"}
    resp = await client.post("/v1/auth/login", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login@example.com"


@pytest.mark.anyio
async def test_login_wrong_password(client: AsyncClient, db_session: AsyncSession):
    user = User(
        email="wrong@example.com",
        password_hash=hash_password("correctpass"),
        full_name="Wrong User",
    )
    db_session.add(user)
    await db_session.commit()

    payload = {"email": "wrong@example.com", "password": "wrongpass"}
    resp = await client.post("/v1/auth/login", json=payload)
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_me_authenticated(client: AsyncClient, db_session: AsyncSession):
    # Kullanıcı oluştur
    user = User(
        email="me@example.com",
        password_hash=hash_password("testpass"),
        full_name="Me User",
    )
    db_session.add(user)
    await db_session.commit()

    # Login yap
    login_resp = await client.post("/v1/auth/login", json={
        "email": "me@example.com", "password": "testpass"
    })
    token = login_resp.json()["access_token"]

    # /me çağır
    resp = await client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


@pytest.mark.anyio
async def test_me_unauthenticated(client: AsyncClient):
    resp = await client.get("/v1/auth/me")
    assert resp.status_code == 401

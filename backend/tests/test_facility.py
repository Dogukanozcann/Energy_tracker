"""
Facility CRUD endpoint testleri.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.database import get_db
from app.models import Base
from app.core.security import hash_password
from app.models.user import User
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


@pytest.fixture
async def auth_headers(client: AsyncClient, db_session: AsyncSession) -> dict[str, str]:
    """Kayıtlı bir kullanıcı oluşturup Bearer token döndürür."""
    user = User(
        email="facility@test.com",
        password_hash=hash_password("testpass123"),
        full_name="Facility Tester",
    )
    db_session.add(user)
    await db_session.commit()

    resp = await client.post("/v1/auth/login", json={
        "email": "facility@test.com",
        "password": "testpass123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# --- Tests ---

@pytest.mark.anyio
async def test_create_facility(client: AsyncClient, auth_headers: dict):
    payload = {
        "name": "Ana Fabrika",
        "facility_type": "factory",
        "city": "İstanbul",
        "district": "Tuzla",
        "area_sqm": 5000.00,
        "num_occupants": 150,
        "operating_hours": 16.0,
    }
    resp = await client.post("/v1/facilities/", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Ana Fabrika"
    assert data["facility_type"] == "factory"
    assert data["city"] == "İstanbul"
    assert data["area_sqm"] == 5000.00
    assert "id" in data


@pytest.mark.anyio
async def test_list_facilities(client: AsyncClient, auth_headers: dict):
    # Önce 2 tesis ekle
    for name in ["Tesis A", "Tesis B"]:
        await client.post("/v1/facilities/", json={"name": name}, headers=auth_headers)

    resp = await client.get("/v1/facilities/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.anyio
async def test_get_facility_by_id(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/v1/facilities/", json={"name": "Detay Tesisi"}, headers=auth_headers
    )
    facility_id = create_resp.json()["id"]

    resp = await client.get(f"/v1/facilities/{facility_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Detay Tesisi"


@pytest.mark.anyio
async def test_get_facility_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get(
        "/v1/facilities/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_update_facility(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/v1/facilities/", json={"name": "Eski İsim"}, headers=auth_headers
    )
    facility_id = create_resp.json()["id"]

    update_resp = await client.put(
        f"/v1/facilities/{facility_id}",
        json={"name": "Yeni İsim", "city": "Ankara"},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Yeni İsim"
    assert update_resp.json()["city"] == "Ankara"


@pytest.mark.anyio
async def test_delete_facility(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/v1/facilities/", json={"name": "Silinecek"}, headers=auth_headers
    )
    facility_id = create_resp.json()["id"]

    delete_resp = await client.delete(
        f"/v1/facilities/{facility_id}", headers=auth_headers
    )
    assert delete_resp.status_code == 204

    # Silindiğini doğrula
    get_resp = await client.get(f"/v1/facilities/{facility_id}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.anyio
async def test_facility_ownership_isolation(client: AsyncClient, db_session: AsyncSession):
    """Kullanıcı A'nın tesisini Kullanıcı B görememeli."""
    # Kullanıcı A
    user_a = User(
        email="user_a@test.com",
        password_hash=hash_password("pass123"),
        full_name="User A",
    )
    db_session.add(user_a)
    await db_session.commit()

    # Kullanıcı A giriş yap
    resp_a = await client.post("/v1/auth/login", json={
        "email": "user_a@test.com", "password": "pass123"
    })
    headers_a = {"Authorization": f"Bearer {resp_a.json()['access_token']}"}

    # Kullanıcı A tesis oluştur
    create_resp = await client.post(
        "/v1/facilities/", json={"name": "A'nın Tesisi"}, headers=headers_a
    )
    facility_id = create_resp.json()["id"]

    # Kullanıcı B
    user_b = User(
        email="user_b@test.com",
        password_hash=hash_password("pass123"),
        full_name="User B",
    )
    db_session.add(user_b)
    await db_session.commit()

    resp_b = await client.post("/v1/auth/login", json={
        "email": "user_b@test.com", "password": "pass123"
    })
    headers_b = {"Authorization": f"Bearer {resp_b.json()['access_token']}"}

    # Kullanıcı B, A'nın tesisini görmeye çalışsın
    get_resp = await client.get(f"/v1/facilities/{facility_id}", headers=headers_b)
    assert get_resp.status_code == 404

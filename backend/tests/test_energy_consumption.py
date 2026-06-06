"""
Energy Consumption API testleri.
Tek kayıt, toplu kayıt, filtreleme, ownership izolasyonu.
"""

from datetime import datetime, timezone, timedelta
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.database import get_db
from app.models import Base
from app.core.security import hash_password
from app.models.user import User
from app.models.facility import Facility
from app.models.energy_source import EnergySource
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Ortak test sabitleri
NOW = datetime.now(timezone.utc)


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
async def seed_data(db_session: AsyncSession) -> dict:
    """Test için ortak kullanıcı + tesis + enerji kaynağı oluşturur."""
    user = User(
        email="energy@test.com",
        password_hash=hash_password("testpass"),
        full_name="Energy Tester",
    )
    db_session.add(user)
    await db_session.flush()

    facility = Facility(
        user_id=user.id,
        name="Test Tesisi",
        city="İstanbul",
    )
    db_session.add(facility)
    await db_session.flush()

    grid = EnergySource(
        name="test_grid",
        category="electricity",
        unit="kWh",
        co2_factor_scope_2=0.706,
        factor_year=2023,
    )
    gas = EnergySource(
        name="test_gas",
        category="natural_gas",
        unit="m³",
        co2_factor_scope_1=2.160,
        factor_year=2021,
    )
    db_session.add_all([grid, gas])
    await db_session.commit()

    return {
        "user": user,
        "facility": facility,
        "grid": grid,
        "gas": gas,
    }


@pytest.fixture
async def auth_headers(client: AsyncClient, db_session: AsyncSession) -> dict:
    resp = await client.post("/v1/auth/login", json={
        "email": "energy@test.com",
        "password": "testpass",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def facility_id(seed_data) -> UUID:
    return seed_data["facility"].id


@pytest.fixture
async def grid_id(seed_data) -> UUID:
    return seed_data["grid"].id


# --- Tests ---

@pytest.mark.anyio
async def test_create_single(
    client: AsyncClient, auth_headers: dict, facility_id, grid_id
):
    payload = {
        "facility_id": str(facility_id),
        "energy_source_id": str(grid_id),
        "recorded_at": NOW.isoformat(),
        "consumption_value": 150.50,
        "unit": "kWh",
        "cost": 300.75,
        "source": "manual",
    }
    resp = await client.post("/v1/energy-consumption/", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["consumption_value"] == 150.50
    assert data["unit"] == "kWh"
    assert data["source"] == "manual"
    assert "id" in data


@pytest.mark.anyio
async def test_create_batch(
    client: AsyncClient, auth_headers: dict, facility_id, grid_id
):
    items = [
        {
            "facility_id": str(facility_id),
            "energy_source_id": str(grid_id),
            "recorded_at": (NOW - timedelta(hours=i)).isoformat(),
            "consumption_value": 100.0 + i,
            "unit": "kWh",
        }
        for i in range(3)
    ]
    resp = await client.post(
        "/v1/energy-consumption/batch",
        json={"items": items},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert len(data) == 3
    assert data[0]["consumption_value"] == 100.0


@pytest.mark.anyio
async def test_list_with_filters(
    client: AsyncClient, auth_headers: dict, facility_id, grid_id
):
    # 5 kayıt ekle (farklı zamanlarda)
    for i in range(5):
        await client.post(
            "/v1/energy-consumption/",
            json={
                "facility_id": str(facility_id),
                "energy_source_id": str(grid_id),
                "recorded_at": (NOW - timedelta(hours=i * 2)).isoformat(),
                "consumption_value": 50.0 + i * 10,
                "unit": "kWh",
            },
            headers=auth_headers,
        )

    # Filtresiz listele
    resp = await client.get(
        "/v1/energy-consumption/",
        params={"facility_id": str(facility_id)},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 5

    # Zaman filtresi ile
    resp2 = await client.get(
        "/v1/energy-consumption/",
        params={
            "facility_id": str(facility_id),
            "date_from": (NOW - timedelta(hours=3)).isoformat(),
        },
        headers=auth_headers,
    )
    assert resp2.status_code == 200
    # 0. ve 2. saat dilimindeki kayıtlar gelmeli (5, 3, 1 saat önce) = 3 kayıt
    # (NOW - 0h, NOW - 2h, NOW - 4h are < 3 saat önce? hayır)
    # Aslında NOW - 0 = şimdi < 3 saat, NOW - 2 = 2 saat önce < 3, NOW - 4 = 4 saat > 3
    # Yani 3 kayıt gelmeli
    assert resp2.json()["total"] == 3


@pytest.mark.anyio
async def test_list_aggregation(
    client: AsyncClient, auth_headers: dict, facility_id, grid_id
):
    # Toplamı test etmek için net değerlerle kayıt ekle
    for val in [100, 200, 300]:
        await client.post(
            "/v1/energy-consumption/",
            json={
                "facility_id": str(facility_id),
                "energy_source_id": str(grid_id),
                "recorded_at": NOW.isoformat(),
                "consumption_value": val,
                "unit": "kWh",
                "cost": val * 2,
            },
            headers=auth_headers,
        )

    resp = await client.get(
        "/v1/energy-consumption/",
        params={"facility_id": str(facility_id)},
        headers=auth_headers,
    )
    data = resp.json()
    assert data["total"] == 3
    assert data["total_value"] == 600.0
    assert data["total_cost"] == 1200.0


@pytest.mark.anyio
async def test_get_by_id(
    client: AsyncClient, auth_headers: dict, facility_id, grid_id
):
    create_resp = await client.post(
        "/v1/energy-consumption/",
        json={
            "facility_id": str(facility_id),
            "energy_source_id": str(grid_id),
            "recorded_at": NOW.isoformat(),
            "consumption_value": 99.9,
            "unit": "kWh",
        },
        headers=auth_headers,
    )
    record_id = create_resp.json()["id"]

    resp = await client.get(f"/v1/energy-consumption/{record_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["consumption_value"] == 99.9


@pytest.mark.anyio
async def test_delete(
    client: AsyncClient, auth_headers: dict, facility_id, grid_id
):
    create_resp = await client.post(
        "/v1/energy-consumption/",
        json={
            "facility_id": str(facility_id),
            "energy_source_id": str(grid_id),
            "recorded_at": NOW.isoformat(),
            "consumption_value": 1.0,
            "unit": "kWh",
        },
        headers=auth_headers,
    )
    record_id = create_resp.json()["id"]

    delete_resp = await client.delete(
        f"/v1/energy-consumption/{record_id}", headers=auth_headers
    )
    assert delete_resp.status_code == 204

    get_resp = await client.get(
        f"/v1/energy-consumption/{record_id}", headers=auth_headers
    )
    assert get_resp.status_code == 404


@pytest.mark.anyio
async def test_ownership_isolation(
    client: AsyncClient, db_session: AsyncSession
):
    """Kullanıcı A B'nin tesisine kayıt ekleyememeli."""
    # Kullanıcı A + tesis + energy source
    user_a = User(
        email="owner_a@test.com",
        password_hash=hash_password("pass"),
        full_name="Owner A",
    )
    db_session.add(user_a)
    await db_session.flush()

    facility_a = Facility(user_id=user_a.id, name="A'nın Tesisi")
    db_session.add(facility_a)
    await db_session.flush()

    src = EnergySource(name="src_a", category="electricity", unit="kWh")
    db_session.add(src)
    await db_session.commit()

    # Kullanıcı B giriş yap
    user_b = User(
        email="owner_b@test.com",
        password_hash=hash_password("pass"),
        full_name="Owner B",
    )
    db_session.add(user_b)
    await db_session.commit()

    resp = await client.post("/v1/auth/login", json={
        "email": "owner_b@test.com", "password": "pass"
    })
    headers_b = {"Authorization": f"Bearer {resp.json()['access_token']}"}

    # Kullanıcı B, A'nın tesisine kayıt eklemeye çalışsın
    payload = {
        "facility_id": str(facility_a.id),
        "energy_source_id": str(src.id),
        "recorded_at": NOW.isoformat(),
        "consumption_value": 100,
        "unit": "kWh",
    }
    resp = await client.post(
        "/v1/energy-consumption/", json=payload, headers=headers_b
    )
    assert resp.status_code == 404

"""
Carbon Calculator + Footprint Aggregation testleri.

Kapsanan senaryolar:
  - Tüketim → Karbon hesaplama (Scope 1, 2, 3)
  - Tekrarlı hesaplama (force=True/False)
  - Toplu hesaplama (batch)
  - Aylık/Yıllık aggregasyon
  - Ownership izolasyonu
"""

from datetime import datetime, timezone, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.database import get_db
from app.models import Base
from app.core.security import hash_password
from app.models.user import User
from app.models.facility import Facility
from app.models.energy_source import EnergySource
from app.models.energy_consumption import EnergyConsumption
from app.models.carbon_footprint import CarbonFootprintItem, CarbonFootprint
from app.services.carbon_calculator import CarbonCalculatorService
from app.services.carbon_footprint_service import CarbonFootprintService
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
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
async def seed(db_session: AsyncSession) -> dict:
    """Kapsamlı test verisi: kullanıcı + tesis + 3 enerji kaynağı + 3 tüketim."""
    user = User(
        email="carbon@test.com",
        password_hash=hash_password("pass"),
        full_name="Carbon Tester",
    )
    db_session.add(user)
    await db_session.flush()

    facility = Facility(
        user_id=user.id,
        name="Karbon Test Tesisi",
        area_sqm=1000.0,
    )
    db_session.add(facility)
    await db_session.flush()

    # Scope 2: Elektrik (co2_factor_scope_2 = 0.706)
    grid = EnergySource(
        name="grid_test", category="electricity", unit="kWh",
        co2_factor_scope_2=0.706,
        co2_factor_source="TÜİK 2023", factor_year=2023,
    )
    # Scope 1: Doğalgaz (co2_factor_scope_1 = 2.160)
    gas = EnergySource(
        name="gas_test", category="natural_gas", unit="m³",
        co2_factor_scope_1=2.160,
        co2_factor_source="IPCC 2021", factor_year=2021,
    )
    # Scope 3: Faktörsüz kaynak
    other = EnergySource(
        name="other_test", category="biomass", unit="kg",
        co2_factor_scope_1=None, co2_factor_scope_2=None,
        is_renewable=True,
    )
    db_session.add_all([grid, gas, other])
    await db_session.flush()

    # 3 tüketim kaydı (her scope için bir tane)
    ec1 = EnergyConsumption(
        facility_id=facility.id, energy_source_id=grid.id,
        recorded_at=NOW, consumption_value=100, unit="kWh",
    )
    ec2 = EnergyConsumption(
        facility_id=facility.id, energy_source_id=gas.id,
        recorded_at=NOW - timedelta(hours=1), consumption_value=50, unit="m³",
    )
    ec3 = EnergyConsumption(
        facility_id=facility.id, energy_source_id=other.id,
        recorded_at=NOW - timedelta(hours=2), consumption_value=200, unit="kg",
    )
    db_session.add_all([ec1, ec2, ec3])
    await db_session.commit()

    return {
        "user": user,
        "facility": facility,
        "grid": grid,
        "gas": gas,
        "other": other,
        "ec1": ec1,  # 100 kWh * 0.706 = 70.6 kg CO2 (scope_2)
        "ec2": ec2,  # 50 m³ * 2.160 = 108 kg CO2 (scope_1)
        "ec3": ec3,  # 200 kg * 0 = 0 kg CO2 (scope_3)
    }


@pytest.fixture
async def auth_headers(client: AsyncClient, db_session: AsyncSession) -> dict:
    resp = await client.post("/v1/auth/login", json={
        "email": "carbon@test.com", "password": "pass"
    })
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# ==================== UNIT TESTS (Service) ====================


@pytest.mark.anyio
async def test_calculate_scope2_electricity(db_session: AsyncSession, seed: dict):
    """100 kWh elektrik = 70.6 kg CO2 (Scope 2)"""
    service = CarbonCalculatorService(db_session)
    item = await service.calculate(
        consumption_id=seed["ec1"].id,
        user_id=seed["user"].id,
    )
    assert item.scope == "scope_2"
    assert float(item.calculated_co2_kg) == 70.6
    assert float(item.co2_factor_used) == 0.706


@pytest.mark.anyio
async def test_calculate_scope1_gas(db_session: AsyncSession, seed: dict):
    """50 m³ doğalgaz = 108 kg CO2 (Scope 1)"""
    service = CarbonCalculatorService(db_session)
    item = await service.calculate(
        consumption_id=seed["ec2"].id,
        user_id=seed["user"].id,
    )
    assert item.scope == "scope_1"
    assert float(item.calculated_co2_kg) == 108.0
    assert float(item.co2_factor_used) == 2.160


@pytest.mark.anyio
async def test_calculate_scope3_no_factor(db_session: AsyncSession, seed: dict):
    """Faktörsüz kaynak = 0 kg CO2 (Scope 3)"""
    service = CarbonCalculatorService(db_session)
    item = await service.calculate(
        consumption_id=seed["ec3"].id,
        user_id=seed["user"].id,
    )
    assert item.scope == "scope_3"
    assert float(item.calculated_co2_kg) == 0.0


@pytest.mark.anyio
async def test_calculate_idempotent_no_force(db_session: AsyncSession, seed: dict):
    """force=False iken ikinci hesaplama mevcut item'i döndürür, yeni oluşturmaz."""
    service = CarbonCalculatorService(db_session)
    item1 = await service.calculate(
        consumption_id=seed["ec1"].id, user_id=seed["user"].id,
    )
    item2 = await service.calculate(
        consumption_id=seed["ec1"].id, user_id=seed["user"].id, force=False,
    )
    assert item1.id == item2.id  # Aynı kayıt


@pytest.mark.anyio
async def test_calculate_force_recalculate(db_session: AsyncSession, seed: dict):
    """force=True ile tüketim değeri değişirse item güncellenir."""
    service = CarbonCalculatorService(db_session)
    # İlk hesaplama
    await service.calculate(
        consumption_id=seed["ec1"].id, user_id=seed["user"].id,
    )

    # Tüketim değerini değiştir
    ec = seed["ec1"]
    ec.consumption_value = 200
    await db_session.flush()

    # force ile yeniden hesapla
    item = await service.calculate(
        consumption_id=seed["ec1"].id, user_id=seed["user"].id, force=True,
    )
    assert float(item.calculated_co2_kg) == 200 * 0.706  # 141.2


@pytest.mark.anyio
async def test_calculate_ownership_blocked(db_session: AsyncSession, seed: dict):
    """Başka kullanıcı hesaplama yapmaya çalışırsa hata alır."""
    other_user = User(
        email="other@test.com", password_hash=hash_password("pass"),
        full_name="Other",
    )
    db_session.add(other_user)
    await db_session.commit()

    service = CarbonCalculatorService(db_session)
    with pytest.raises(ValueError, match="size ait değil"):
        await service.calculate(
            consumption_id=seed["ec1"].id,
            user_id=other_user.id,
        )


# ==================== BATCH TESTS ====================


@pytest.mark.anyio
async def test_calculate_batch(db_session: AsyncSession, seed: dict):
    """Batch hesaplama tüm kayıtları işler."""
    service = CarbonCalculatorService(db_session)
    count, total = await service.calculate_batch(
        facility_id=seed["facility"].id,
        user_id=seed["user"].id,
    )
    assert count == 3
    assert total == 70.6 + 108.0 + 0.0


@pytest.mark.anyio
async def test_calculate_batch_skip_existing(db_session: AsyncSession, seed: dict):
    """Batch, daha önce hesaplanmış kayıtları atlar (force=False)."""
    service = CarbonCalculatorService(db_session)
    # Önce birini hesapla
    await service.calculate(consumption_id=seed["ec1"].id, user_id=seed["user"].id)

    # Batch çağır (sadece hesaplanmamış olanlar)
    count, total = await service.calculate_batch(
        facility_id=seed["facility"].id,
        user_id=seed["user"].id,
        force=False,
    )
    assert count == 2  # ec2 ve ec3


# ==================== AGGREGATION TESTS ====================


@pytest.mark.anyio
async def test_generate_monthly_footprint(db_session: AsyncSession, seed: dict):
    """Aylık aggregasyon doğru toplamları üretir."""
    # Önce tüm tüketimleri hesapla
    calc = CarbonCalculatorService(db_session)
    await calc.calculate_batch(seed["facility"].id, seed["user"].id)

    # Aylık özet oluştur
    fp = CarbonFootprintService(db_session)
    footprint = await fp.generate_monthly(
        facility_id=seed["facility"].id,
        user_id=seed["user"].id,
        year=NOW.year,
        month=NOW.month,
    )
    assert float(footprint.total_co2_kg) == 70.6 + 108.0
    assert float(footprint.scope_1_co2_kg) == 108.0
    assert float(footprint.scope_2_co2_kg) == 70.6
    assert float(footprint.scope_3_co2_kg) == 0.0
    assert footprint.status == "draft"


# ==================== API TESTS ====================


@pytest.mark.anyio
async def test_api_calculate_single(
    client: AsyncClient, auth_headers: dict, seed: dict
):
    resp = await client.post(
        "/v1/carbon/calculate",
        json={"consumption_id": str(seed["ec1"].id)},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["scope"] == "scope_2"
    assert data["calculated_co2_kg"] == 70.6


@pytest.mark.anyio
async def test_api_calculate_batch(
    client: AsyncClient, auth_headers: dict, seed: dict
):
    resp = await client.post(
        "/v1/carbon/calculate-batch",
        json={"facility_id": str(seed["facility"].id)},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["processed"] == 3
    assert data["total_co2_kg"] == 178.6


@pytest.mark.anyio
async def test_api_generate_footprint(
    client: AsyncClient, auth_headers: dict, seed: dict
):
    # Önce hesapla
    await client.post(
        "/v1/carbon/calculate-batch",
        json={"facility_id": str(seed["facility"].id)},
        headers=auth_headers,
    )
    # Özet oluştur
    resp = await client.post(
        "/v1/carbon/footprints/generate",
        json={
            "facility_id": str(seed["facility"].id),
            "year": NOW.year,
            "month": NOW.month,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["total_co2_kg"] == 178.6
    assert data["intensity_per_area"] == 0.1786  # 178.6 / 1000 m²


@pytest.mark.anyio
async def test_api_list_items(
    client: AsyncClient, auth_headers: dict, seed: dict
):
    # Önce hesapla
    await client.post(
        "/v1/carbon/calculate-batch",
        json={"facility_id": str(seed["facility"].id)},
        headers=auth_headers,
    )
    resp = await client.get(
        "/v1/carbon/items",
        params={"facility_id": str(seed["facility"].id)},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert data["total_co2_kg"] == 178.6


@pytest.mark.anyio
async def test_api_list_footprints(
    client: AsyncClient, auth_headers: dict, seed: dict
):
    await client.post(
        "/v1/carbon/calculate-batch",
        json={"facility_id": str(seed["facility"].id)},
        headers=auth_headers,
    )
    await client.post(
        "/v1/carbon/footprints/generate",
        json={
            "facility_id": str(seed["facility"].id),
            "year": NOW.year,
            "month": NOW.month,
        },
        headers=auth_headers,
    )
    resp = await client.get(
        "/v1/carbon/footprints",
        params={"facility_id": str(seed["facility"].id)},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1

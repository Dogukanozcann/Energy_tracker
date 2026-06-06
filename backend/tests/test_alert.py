"""
Alert & Anomaly Detection testleri.

Kapsam:
  - Manuel uyarı CRUD
  - Status lifecycle (new → acknowledged → resolved/dismissed)
  - Geçersiz status geçişleri
  - Anomali tespit motoru (baseline karşılaştırması)
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
from app.models.alert import Alert
from app.services.anomaly_detector import AnomalyDetectorService
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
    """Kullanıcı + tesis + enerji kaynağı."""
    user = User(
        email="alert@test.com",
        password_hash=hash_password("pass"),
        full_name="Alert Tester",
    )
    db_session.add(user)
    await db_session.flush()

    facility = Facility(user_id=user.id, name="Alert Tesisi")
    db_session.add(facility)
    await db_session.flush()

    grid = EnergySource(
        name="alert_grid", category="electricity", unit="kWh",
        co2_factor_scope_2=0.706,
    )
    db_session.add(grid)
    await db_session.commit()

    return {"user": user, "facility": facility, "grid": grid}


@pytest.fixture
async def auth_headers(client: AsyncClient, db_session: AsyncSession) -> dict:
    resp = await client.post("/v1/auth/login", json={
        "email": "alert@test.com", "password": "pass"
    })
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# ==================== CRUD TESTS ====================


@pytest.mark.anyio
async def test_create_alert(client: AsyncClient, auth_headers: dict, seed: dict):
    payload = {
        "facility_id": str(seed["facility"].id),
        "title": "Anomali Tespiti",
        "description": "Tüketim %30 arttı",
        "severity": "high",
        "category": "anomaly",
        "detected_value": 150.0,
        "expected_value": 100.0,
        "deviation_percent": 50.0,
        "recommendation_text": "Ekipmanı kontrol edin.",
    }
    resp = await client.post("/v1/alerts/", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Anomali Tespiti"
    assert data["severity"] == "high"
    assert data["is_auto_generated"] is False
    assert data["status"] == "new"
    assert "id" in data


@pytest.mark.anyio
async def test_list_alerts(client: AsyncClient, auth_headers: dict, seed: dict):
    # 3 uyarı oluştur
    for title in ["Uyarı A", "Uyarı B", "Uyarı C"]:
        await client.post(
            "/v1/alerts/",
            json={"facility_id": str(seed["facility"].id), "title": title, "category": "anomaly"},
            headers=auth_headers,
        )
    resp = await client.get(
        "/v1/alerts/",
        params={"facility_id": str(seed["facility"].id)},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 3
    assert resp.json()["new_count"] == 3


@pytest.mark.anyio
async def test_list_alerts_filtered(client: AsyncClient, auth_headers: dict, seed: dict):
    # Farklı severities
    await client.post(
        "/v1/alerts/",
        json={"facility_id": str(seed["facility"].id), "title": "Kritik", "severity": "critical", "category": "anomaly"},
        headers=auth_headers,
    )
    await client.post(
        "/v1/alerts/",
        json={"facility_id": str(seed["facility"].id), "title": "Düşük", "severity": "low", "category": "anomaly"},
        headers=auth_headers,
    )
    resp = await client.get(
        "/v1/alerts/",
        params={"facility_id": str(seed["facility"].id), "severity": "critical"},
        headers=auth_headers,
    )
    assert resp.json()["total"] == 1


@pytest.mark.anyio
async def test_get_alert(client: AsyncClient, auth_headers: dict, seed: dict):
    create_resp = await client.post(
        "/v1/alerts/",
        json={"facility_id": str(seed["facility"].id), "title": "Detay", "category": "anomaly"},
        headers=auth_headers,
    )
    alert_id = create_resp.json()["id"]

    resp = await client.get(f"/v1/alerts/{alert_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "Detay"


@pytest.mark.anyio
async def test_delete_alert(client: AsyncClient, auth_headers: dict, seed: dict):
    create_resp = await client.post(
        "/v1/alerts/",
        json={"facility_id": str(seed["facility"].id), "title": "Silinecek", "category": "anomaly"},
        headers=auth_headers,
    )
    alert_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/v1/alerts/{alert_id}", headers=auth_headers)
    assert del_resp.status_code == 204


# ==================== STATUS LIFECYCLE ====================


@pytest.mark.anyio
async def test_status_acknowledge(client: AsyncClient, auth_headers: dict, seed: dict):
    create_resp = await client.post(
        "/v1/alerts/",
        json={"facility_id": str(seed["facility"].id), "title": "Ack Test", "category": "anomaly"},
        headers=auth_headers,
    )
    alert_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/v1/alerts/{alert_id}/status",
        json={"status": "acknowledged"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "acknowledged"


@pytest.mark.anyio
async def test_status_full_lifecycle(client: AsyncClient, auth_headers: dict, seed: dict):
    create_resp = await client.post(
        "/v1/alerts/",
        json={"facility_id": str(seed["facility"].id), "title": "Full Cycle", "category": "anomaly"},
        headers=auth_headers,
    )
    alert_id = create_resp.json()["id"]

    # new → acknowledged
    await client.patch(
        f"/v1/alerts/{alert_id}/status",
        json={"status": "acknowledged"}, headers=auth_headers,
    )
    # acknowledged → resolved
    resp = await client.patch(
        f"/v1/alerts/{alert_id}/status",
        json={"status": "resolved"}, headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "resolved"


@pytest.mark.anyio
async def test_invalid_transition(client: AsyncClient, auth_headers: dict, seed: dict):
    """new → resolved (acknowledged atlanamaz)."""
    create_resp = await client.post(
        "/v1/alerts/",
        json={"facility_id": str(seed["facility"].id), "title": "Invalid", "category": "anomaly"},
        headers=auth_headers,
    )
    alert_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/v1/alerts/{alert_id}/status",
        json={"status": "resolved"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


# ==================== DETECTION ENGINE ====================


@pytest.mark.anyio
async def test_detection_no_anomaly(db_session: AsyncSession, seed: dict):
    """Tüm değerler normale yakınsa anomali oluşmaz."""
    fac, grid = seed["facility"], seed["grid"]

    # Baseline verisi: 7 günlük düzenli veri
    for day in range(7, 0, -1):
        for hour in range(6, 22):
            ec = EnergyConsumption(
                facility_id=fac.id, energy_source_id=grid.id,
                recorded_at=NOW - timedelta(days=day, hours=NOW.hour - hour),
                consumption_value=100.0,
                unit="kWh",
            )
            db_session.add(ec)
    # Son 24 saat: yine 100
    ec = EnergyConsumption(
        facility_id=fac.id, energy_source_id=grid.id,
        recorded_at=NOW - timedelta(hours=1),
        consumption_value=105.0,  # Sadece %5 sapma
        unit="kWh",
    )
    db_session.add(ec)
    await db_session.commit()

    detector = AnomalyDetectorService(db_session)
    alerts = await detector.detect(
        facility_id=fac.id,
        user_id=seed["user"].id,
        deviation_threshold=20.0,
    )
    assert len(alerts) == 0  # %5 sapma, eşik %20


@pytest.mark.anyio
async def test_detection_creates_alert(db_session: AsyncSession, seed: dict):
    """%50+ sapma anomali oluşturur."""
    fac, grid = seed["facility"], seed["grid"]

    # Baseline: 100 birim
    for day in range(7, 0, -1):
        ec = EnergyConsumption(
            facility_id=fac.id, energy_source_id=grid.id,
            recorded_at=NOW - timedelta(days=day, hours=2),
            consumption_value=100.0,
            unit="kWh",
        )
        db_session.add(ec)

    # Anomali: 250 birim (%150 sapma)
    ec = EnergyConsumption(
        facility_id=fac.id, energy_source_id=grid.id,
        recorded_at=NOW - timedelta(hours=2),
        consumption_value=250.0,
        unit="kWh",
    )
    db_session.add(ec)
    await db_session.commit()

    detector = AnomalyDetectorService(db_session)
    alerts = await detector.detect(
        facility_id=fac.id,
        user_id=seed["user"].id,
        deviation_threshold=20.0,
    )
    assert len(alerts) == 1
    assert alerts[0].severity == "critical"  # %150 sapma → critical
    assert alerts[0].category == "anomaly"
    assert alerts[0].is_auto_generated is True
    assert float(alerts[0].deviation_percent) >= 100


@pytest.mark.anyio
async def test_detection_ownership_blocked(db_session: AsyncSession, seed: dict):
    """Başka kullanıcı anomali taraması yapamaz."""
    other = User(
        email="other_alert@test.com",
        password_hash=hash_password("pass"),
        full_name="Other",
    )
    db_session.add(other)
    await db_session.commit()

    detector = AnomalyDetectorService(db_session)
    with pytest.raises(ValueError, match="size ait değil"):
        await detector.detect(
            facility_id=seed["facility"].id,
            user_id=other.id,
        )


# ==================== API DETECTION ====================


@pytest.mark.anyio
async def test_api_detect_anomaly(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, seed: dict
):
    """API üzerinden anomali tespiti."""
    fac, grid = seed["facility"], seed["grid"]

    for day in range(7, 0, -1):
        ec = EnergyConsumption(
            facility_id=fac.id, energy_source_id=grid.id,
            recorded_at=NOW - timedelta(days=day, hours=3),
            consumption_value=100.0, unit="kWh",
        )
        db_session.add(ec)

    ec = EnergyConsumption(
        facility_id=fac.id, energy_source_id=grid.id,
        recorded_at=NOW - timedelta(hours=3),
        consumption_value=300.0, unit="kWh",
    )
    db_session.add(ec)
    await db_session.commit()

    resp = await client.post(
        "/v1/alerts/detect",
        json={
            "facility_id": str(fac.id),
            "deviation_threshold": 20.0,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["alerts_created"] >= 1

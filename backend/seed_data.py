"""
Seed script — Veritabanını test verileriyle doldurur.

Kullanım:
    cd backend
    python seed_data.py

Oluşturduğu:
  - Admin test kullanıcısı (test@enerji.com / 123456 — role=admin)
  - Viewer test kullanıcısı (izleyici@enerji.com / 123456 — role=viewer)
  - 1 tesis (İstanbul Ofis)
  - 8 enerji kaynağı (Elektrik, Doğalgaz, Güneş, Dizel, Benzin, Su, Kömür, LPG)
  - 3 aylık saatlik tüketim verisi (~6500 kayıt)
  - Karbon ayak izi hesaplamaları
  - Sistem ayarları
  - Denetim kayıtları (admin panodaki log sayfası için)
"""

import asyncio
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.database import async_session_factory, engine
from app.core.security import hash_password
from app.models import Base
from app.models import (
    User,
    UserPreference,
    Facility,
    EnergySource,
    EnergyConsumption,
    CarbonFootprintItem,
    SystemSetting,
    AuditLog,
)


# ──────────────────────────────────────────────
# VERİ
# ──────────────────────────────────────────────

ENERGY_SOURCES = [
    {
        "name": "grid_electricity",
        "name_tr": "Şebeke Elektriği",
        "category": "electricity",
        "unit": "kWh",
        "formula_type": "factor",
        "co2_factor_scope_2": 0.45,
        "co2_factor_source": "TÜİK 2024 - Türkiye elektrik şebeke faktörü (0.45 kg CO2e/kWh)",
        "factor_year": 2024,
        "is_renewable": False,
        "is_active": True,
    },
    {
        "name": "natural_gas",
        "name_tr": "Doğalgaz",
        "category": "natural_gas",
        "unit": "m³",
        "formula_type": "dual_unit",
        "unit_alt": "kWh",
        "co2_factor_scope_1": 2.02,
        "co2_factor_scope_1_alt": 0.183,
        "co2_factor_source": "IPCC 2024 - Doğalgaz: 2.02 kg CO2e/m³, 0.183 kg CO2e/kWh",
        "factor_year": 2024,
        "is_renewable": False,
        "is_active": True,
    },
    {
        "name": "solar_pv",
        "name_tr": "Güneş (PV)",
        "category": "solar",
        "unit": "kWh",
        "formula_type": "factor",
        "co2_factor_scope_2": 0.0,
        "co2_factor_source": "Yenilenebilir - sıfır emisyon",
        "factor_year": 2024,
        "is_renewable": True,
        "is_active": True,
    },
    {
        "name": "diesel",
        "name_tr": "Dizel (Araç Yakıtı)",
        "category": "diesel",
        "unit": "litre",
        "formula_type": "fuel",
        "fuel_density": 0.835,
        "fuel_carbon_ratio": 0.862,
        "fuel_co2_per_liter": 2.64,
        "co2_factor_source": "E_CO2 = V * 0.835 * 0.862 * (44/12) ≈ 2.64 kg CO2e/L",
        "factor_year": 2024,
        "is_renewable": False,
        "is_active": True,
    },
    {
        "name": "gasoline",
        "name_tr": "Benzin (Araç Yakıtı)",
        "category": "gasoline",
        "unit": "litre",
        "formula_type": "fuel",
        "fuel_density": 0.740,
        "fuel_carbon_ratio": 0.870,
        "fuel_co2_per_liter": 2.36,
        "co2_factor_source": "E_CO2 = V * 0.740 * 0.870 * (44/12) ≈ 2.36 kg CO2e/L",
        "factor_year": 2024,
        "is_renewable": False,
        "is_active": True,
    },
    {
        "name": "water",
        "name_tr": "Su Tüketimi",
        "category": "water",
        "unit": "m³",
        "formula_type": "factor",
        "co2_factor_scope_1": 1.04,
        "co2_factor_source": "Su temini (0.34) + Atıksu arıtma (0.70) = 1.04 kg CO2e/m³",
        "factor_year": 2024,
        "is_renewable": False,
        "is_active": True,
    },
    {
        "name": "coal",
        "name_tr": "Kömür",
        "category": "coal",
        "unit": "kg",
        "formula_type": "factor",
        "co2_factor_scope_1": 2.42,
        "co2_factor_source": "IPCC 2024 - Taş kömürü: 2.42 kg CO2e/kg",
        "factor_year": 2024,
        "is_renewable": False,
        "is_active": True,
    },
    {
        "name": "lpg",
        "name_tr": "LPG",
        "category": "lpg",
        "unit": "kg",
        "formula_type": "factor",
        "co2_factor_scope_1": 2.98,
        "co2_factor_source": "IPCC 2024 - LPG: 2.98 kg CO2e/kg",
        "factor_year": 2024,
        "is_renewable": False,
        "is_active": True,
    },
]


SYSTEM_SETTINGS = [
    {
        "key": "carbon.factor_year",
        "value": "2024",
        "description": "Karbon hesaplamalarında kullanılan güncel faktör yılı",
        "category": "carbon",
    },
    {
        "key": "carbon.default_methodology",
        "value": "ipcc_2024",
        "description": "Varsayılan karbon hesaplama metodolojisi",
        "category": "carbon",
    },
    {
        "key": "general.currency",
        "value": "TRY",
        "description": "Sistem genel para birimi",
        "category": "general",
    },
    {
        "key": "general.energy_unit",
        "value": "kWh",
        "description": "Varsayılan enerji birimi",
        "category": "general",
    },
    {
        "key": "alert.anomaly_threshold",
        "value": "2.5",
        "description": "Anomali tespiti için standart sapma eşik değeri",
        "category": "alert",
    },
    {
        "key": "alert.max_daily_alerts",
        "value": "10",
        "description": "Tesis başına günlük maksimum uyarı sayısı",
        "category": "alert",
    },
    {
        "key": "system.report_retention_days",
        "value": "365",
        "description": "Raporların saklanma süresi (gün)",
        "category": "system",
    },
    {
        "key": "system.session_timeout_minutes",
        "value": "60",
        "description": "Kullanıcı oturum zaman aşımı süresi",
        "category": "system",
    },
]


def generate_consumption(base: float, hour: int, noise: float = 0.15) -> float:
    """Günün saatine göre gerçekçi tüketim üretir."""
    # Mesai saatleri (08-18) = yüksek, gece = düşük
    if 8 <= hour <= 18:
        multiplier = 1.0 + 0.5 * (1 - abs(hour - 13) / 6)
    elif 19 <= hour <= 23:
        multiplier = 0.6
    else:  # 00-07
        multiplier = 0.3
    jitter = 1 + random.uniform(-noise, noise)
    return round(base * multiplier * jitter, 2)


# ──────────────────────────────────────────────
# SEED
# ──────────────────────────────────────────────

async def seed():
    # Tabloları oluştur (yoksa)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        # 1. Kullanıcı var mı kontrol et
        existing = await db.execute(
            select(User).where(User.email == "test@enerji.com")
        )
        if existing.scalar_one_or_none():
            print("! Veritabaninda zaten veri var. Tekrar calistirmak icin DB'yi silip tekrar dene:")
            print("   del energy_tracker.db")
            return

        print("Seed basladi...")

        # ── ADMIN KULLANICI ──
        admin_user = User(
            email="test@enerji.com",
            password_hash=hash_password("123456"),
            full_name="Test Kullanıcısı",
            company_name="Enerji A.Ş.",
            sector="teknoloji",
            city="İstanbul",
            district="Kadıköy",
            user_type="business",
            role="admin",
            is_active=True,
            email_verified_at=datetime.now(timezone.utc),
        )
        db.add(admin_user)
        await db.flush()

        # ── ADMIN TERCİHLERİ ──
        db.add(UserPreference(
            user_id=admin_user.id,
            language="tr",
            timezone="Europe/Istanbul",
            energy_unit="kWh",
            currency="TRY",
            weekly_report=True,
        ))
        await db.flush()
        print(f"  [OK] Admin kullanici: test@enerji.com / 123456")

        # ── VIEWER KULLANICI ──
        viewer_user = User(
            email="izleyici@enerji.com",
            password_hash=hash_password("123456"),
            full_name="İzleyici Kullanıcı",
            company_name="Enerji A.Ş.",
            sector="teknoloji",
            city="Ankara",
            district="Çankaya",
            user_type="business",
            role="viewer",
            is_active=True,
            email_verified_at=datetime.now(timezone.utc),
        )
        db.add(viewer_user)
        await db.flush()

        db.add(UserPreference(
            user_id=viewer_user.id,
            language="tr",
            timezone="Europe/Istanbul",
            energy_unit="kWh",
            currency="TRY",
            weekly_report=False,
        ))
        await db.flush()
        print(f"  [OK] Viewer kullanici: izleyici@enerji.com / 123456")

        # ── TESİS ──
        facility = Facility(
            user_id=admin_user.id,
            name="İstanbul Merkez Ofis",
            description="Ana ofis binası - enerji takibi",
            facility_type="office",
            city="İstanbul",
            district="Kadıköy",
            country="Türkiye",
            area_sqm=1250.0,
            heated_area_sqm=950.0,
            num_floors=5,
            num_occupants=85,
            operating_hours=10,
            is_active=True,
        )
        db.add(facility)
        await db.flush()
        print(f"  [OK] Tesis: {facility.name}")

        # ── ENERJİ KAYNAKLARI ──
        sources = {}
        for s in ENERGY_SOURCES:
            src = EnergySource(**s)
            db.add(src)
            await db.flush()
            sources[s["name"]] = src
        print(f"  [OK] Enerji kaynaklari: {', '.join(sources.keys())}")

        # ── TÜKETİM VERİSİ (3 AY) ──
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=90)
        start_date = start_date.replace(minute=0, second=0, microsecond=0)

        consumption_bases = {
            "grid_electricity": 45.0,
            "natural_gas": 8.5,
            "solar_pv": 12.0,
            "diesel": 0.0,     # araç yakıtı - hafta içi günlük
            "gasoline": 0.0,   # araç yakıtı - hafta içi günlük
            "water": 0.15,     # m³/saat (sürekli düşük akış)
            "coal": 0.0,       # örnek için boş
            "lpg": 0.0,        # örnek için boş
        }

        total_records = 0
        current = start_date

        while current < now:
            hour = current.hour
            month = current.month

            # Kış aylarında doğalgaz daha yüksek
            gas_multiplier = 1.5 if month in (12, 1, 2) else 1.0
            # Güneş sadece 07-19 arası üretir, kışın daha az
            solar_active = 7 <= hour <= 18
            solar_multiplier = 0.6 if month in (12, 1, 2) else 1.0

            for src_name, src_obj in sources.items():
                base = consumption_bases.get(src_name, 0)

                if src_name == "grid_electricity":
                    value = generate_consumption(base, hour)
                    cost = round(value * 2.5, 2)
                    cons_type = "consumption"
                elif src_name == "natural_gas":
                    value = generate_consumption(base * gas_multiplier, hour)
                    cost = round(value * 4.2, 2)
                    cons_type = "consumption"
                elif src_name == "solar_pv":
                    if not solar_active or random.random() < 0.15:
                        continue
                    value = generate_consumption(
                        base * solar_multiplier * random.uniform(0.4, 1.0), hour
                    )
                    cost = 0
                    cons_type = "production"
                elif src_name in ("diesel", "gasoline"):
                    # Araç yakıtı: hafta içi günde 1 kayıt (sabah 08:00)
                    if current.weekday() >= 5 or hour != 8 or random.random() > 0.15:
                        continue
                    liters = {
                        "diesel": round(random.uniform(8, 25), 1),
                        "gasoline": round(random.uniform(6, 18), 1),
                    }
                    value = liters[src_name]
                    cost = round(value * (28.5 if src_name == "gasoline" else 32.0), 2)
                    cons_type = "consumption"
                elif src_name == "water":
                    value = round(base * random.uniform(0.3, 1.8), 2)
                    cost = round(value * 15.0, 2)
                    cons_type = "consumption"
                elif src_name in ("coal", "lpg"):
                    # Bu kaynaklar için günlük 1 kayıt (örnek)
                    if hour != 10 or random.random() > 0.1:
                        continue
                    vals = {"coal": round(random.uniform(20, 80), 1), "lpg": round(random.uniform(5, 20), 1)}
                    value = vals[src_name]
                    cost = round(value * (8.0 if src_name == "coal" else 12.0), 2)
                    cons_type = "consumption"
                else:
                    continue  # Bilinmeyen kaynak atla

                # Hafta sonu düşük tüketim (sadece consumption tipinde)
                if cons_type == "consumption" and current.weekday() >= 5 and src_name not in ("diesel", "gasoline"):
                    value = round(value * 0.3, 2)
                    if value < 0.5:
                        continue

                record = EnergyConsumption(
                    facility_id=facility.id,
                    energy_source_id=src_obj.id,
                    recorded_at=current,
                    consumption_value=value,
                    unit=src_obj.unit,
                    cost=cost if src_name != "solar_pv" else None,
                    source="manual",
                    consumption_type=cons_type,
                    is_estimated=False,
                )
                db.add(record)
                total_records += 1

            current += timedelta(hours=1)

        await db.flush()
        print(f"  [OK] Tuketim kaydi: {total_records} adet")

        # ── KARBON HESAPLAMASI ──
        cons_list = await db.execute(
            select(EnergyConsumption).where(
                EnergyConsumption.facility_id == facility.id
            )
        )
        cons_records = cons_list.scalars().all()

        carbon_count = 0
        for c in cons_records:
            src = sources.get(
                [k for k, v in sources.items() if v.id == c.energy_source_id][0]
            )

            if src.co2_factor_scope_1 is not None:
                scope = "scope_1"
                factor = float(src.co2_factor_scope_1)
            elif src.co2_factor_scope_2 is not None:
                scope = "scope_2"
                factor = float(src.co2_factor_scope_2)
            else:
                scope = "scope_3"
                factor = 0.0

            item = CarbonFootprintItem(
                energy_consumption_id=c.id,
                energy_source_id=c.energy_source_id,
                scope=scope,
                consumption_amount=float(c.consumption_value),
                consumption_unit=c.unit,
                co2_factor_used=factor,
                calculated_co2_kg=round(float(c.consumption_value) * factor, 4),
                factor_source=src.co2_factor_source,
            )
            db.add(item)
            carbon_count += 1

        await db.commit()
        print(f"  [OK] Karbon hesaplamasi: {carbon_count} adet")

        # ── SİSTEM AYARLARI ──
        for s in SYSTEM_SETTINGS:
            existing_setting = await db.execute(
                select(SystemSetting).where(SystemSetting.key == s["key"])
            )
            if not existing_setting.scalar_one_or_none():
                db.add(SystemSetting(**s))
        await db.flush()
        print(f"  [OK] Sistem ayarlari: {len(SYSTEM_SETTINGS)} adet")

        # ── DENETİM KAYITLARI ──
        audit_logs = [
            AuditLog(
                user_id=admin_user.id,
                user_email=admin_user.email,
                action="create",
                resource="energy_source",
                resource_id=str(sources["grid_electricity"].id),
                details="Seed ile şebeke elektriği kaynağı oluşturuldu",
                ip_address="127.0.0.1",
            ),
            AuditLog(
                user_id=admin_user.id,
                user_email=admin_user.email,
                action="create",
                resource="energy_source",
                resource_id=str(sources["natural_gas"].id),
                details="Seed ile doğalgaz kaynağı oluşturuldu",
                ip_address="127.0.0.1",
            ),
            AuditLog(
                user_id=admin_user.id,
                user_email=admin_user.email,
                action="create",
                resource="energy_source",
                resource_id=str(sources["solar_pv"].id),
                details="Seed ile güneş enerjisi kaynağı oluşturuldu",
                ip_address="127.0.0.1",
            ),
            AuditLog(
                user_id=admin_user.id,
                user_email=admin_user.email,
                action="create",
                resource="user",
                resource_id=str(admin_user.id),
                details="Admin kullanıcı oluşturuldu: test@enerji.com",
                ip_address="127.0.0.1",
            ),
            AuditLog(
                user_id=admin_user.id,
                user_email=admin_user.email,
                action="create",
                resource="user",
                resource_id=str(viewer_user.id),
                details="Viewer kullanıcı oluşturuldu: izleyici@enerji.com",
                ip_address="127.0.0.1",
            ),
            AuditLog(
                user_id=admin_user.id,
                user_email=admin_user.email,
                action="create",
                resource="setting",
                details=f"{len(SYSTEM_SETTINGS)} adet sistem ayarı seed ile oluşturuldu",
                ip_address="127.0.0.1",
            ),
            AuditLog(
                user_id=admin_user.id,
                user_email=admin_user.email,
                action="create",
                resource="facility",
                resource_id=str(facility.id),
                details="Tesis oluşturuldu: İstanbul Merkez Ofis",
                ip_address="127.0.0.1",
            ),
            AuditLog(
                user_id=admin_user.id,
                user_email=admin_user.email,
                action="update",
                resource="setting",
                details="Varsayılan sistem ayarları güncellendi",
                ip_address="127.0.0.1",
            ),
        ]
        for log in audit_logs:
            db.add(log)
        await db.commit()
        print(f"  [OK] Denetim kayitlari: {len(audit_logs)} adet")

        print()
        print("==============================")
        print("  Seed tamamlandi!")
        print()
        print("  Giris bilgileri:")
        print("    Admin: test@enerji.com / 123456 (role=admin)")
        print("    Viewer: izleyici@enerji.com / 123456 (role=viewer)")
        print()
        print("  Frontend: http://localhost:3000")
        print("  Backend:  http://localhost:8000")
        print("==============================")


if __name__ == "__main__":
    asyncio.run(seed())

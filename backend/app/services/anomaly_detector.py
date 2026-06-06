"""
Anomali Tespit Motoru.

İstatistiksel yöntemle enerji tüketimindeki anomalileri bulur:
1. Son N saatlik tüketimi al
2. Aynı saat/dilim için geçmiş N günlük ortalamayı hesapla (baseline)
3. Sapma yüzdesi eşiği aşarsa uyarı oluştur

Kullandığı yöntem: Zaman-serisi baseline karşılaştırması
  (basit ama explainable — regresyon/ML gerektirmez, her tesiste çalışır)
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.energy_consumption import EnergyConsumption
from app.models.energy_source import EnergySource
from app.models.facility import Facility


class AnomalyDetectorService:
    """
    Enerji tüketim anomalilerini tespit eder ve Alert kaydı oluşturur.

    Varsayılan parametreler:
      - baseline_days:      Geçmiş kaç günlük veri baz alınacak (7)
      - deviation_threshold: % kaç sapma anomali sayılacak (20)
      - min_data_points:    En az kaç veri noktası gerekli (3)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        facility_id: UUID,
        user_id: UUID,
        energy_source_id: UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        deviation_threshold: float = 20.0,
        baseline_days: int = 7,
    ) -> list[Alert]:
        """
        Belirtilen tesiste anomali taraması yapar.

        Parametreler:
          facility_id:       Tesis ID
          user_id:           Ownership doğrulaması
          energy_source_id:  Sadece belirli kaynak (opsiyonel)
          date_from:         Taranacak aralık başlangıcı
          date_to:           Taranacak aralık bitişi
          deviation_threshold:  % eşik (örn. 20 = %20 üzeri anomali)
          baseline_days:     Geçmiş veri gün sayısı

        Dönüş: Oluşturulan Alert nesnelerinin listesi
        """
        # Ownership
        q = select(Facility.id).where(
            Facility.id == facility_id, Facility.user_id == user_id
        )
        if (await self.db.execute(q)).scalar_one_or_none() is None:
            raise ValueError("Tesis bulunamadı veya size ait değil.")

        # Zaman aralığı (varsayılan: son 24 saat)
        now = datetime.now(timezone.utc)
        date_to = date_to or now
        date_from = date_from or (now - timedelta(hours=24))

        # Baseline dönemi: aynı saat dilimi için geçmiş veri
        baseline_start = date_from - timedelta(days=baseline_days)

        # Taranacak kayıtları getir
        filters = [
            EnergyConsumption.facility_id == facility_id,
            EnergyConsumption.recorded_at >= date_from,
            EnergyConsumption.recorded_at <= date_to,
        ]
        if energy_source_id:
            filters.append(EnergyConsumption.energy_source_id == energy_source_id)

        ec_q = (
            select(
                EnergyConsumption.id,
                EnergyConsumption.energy_source_id,
                EnergyConsumption.recorded_at,
                EnergyConsumption.consumption_value,
                EnergyConsumption.unit,
                EnergySource.name,
            )
            .join(EnergySource, EnergySource.id == EnergyConsumption.energy_source_id)
            .where(*filters)
            .order_by(EnergyConsumption.recorded_at.asc())
        )
        rows = list((await self.db.execute(ec_q)).all())

        if not rows:
            return []

        alerts_created: list[Alert] = []
        for row in rows:
            # Her kayıt için aynı saat-dakika diliminin baseline ortalamasını bul
            avg = await self._get_baseline(
                facility_id=facility_id,
                energy_source_id=row.energy_source_id,
                target_time=row.recorded_at,
                baseline_start=baseline_start,
                baseline_end=date_from,
            )

            if avg is None or avg <= 0:
                continue  # Yeterli baseline verisi yok

            value = float(row.consumption_value)
            deviation_pct = round((value - avg) / avg * 100, 2)

            # Sadece yüksek sapmaları (threshold üstü) uyarıya çevir
            if deviation_pct <= deviation_threshold:
                continue

            # Aynı kaynaktan son N saatte benzer uyarı var mı kontrol et
            if await self._has_recent_alert(facility_id, row.energy_source_id):
                continue

            # Severity belirle
            severity = self._classify_severity(deviation_pct)

            alert = Alert(
                facility_id=facility_id,
                energy_source_id=row.energy_source_id,
                title=f"Anomali: {row.name} tüketimi %{abs(deviation_pct):.0f} arttı",
                description=(
                    f"{row.unit} cinsinden tüketim {value} olarak ölçüldü. "
                    f"Aynı dönem ortalaması {avg:.2f} {row.unit}. "
                    f"Sapma: %{deviation_pct:+.2f}."
                ),
                severity=severity,
                category="anomaly",
                detected_value=value,
                expected_value=round(avg, 4),
                deviation_percent=deviation_pct,
                recommendation_text=self._get_recommendation(severity),
                is_auto_generated=True,
            )
            self.db.add(alert)
            alerts_created.append(alert)

        if alerts_created:
            await self.db.flush()

        return alerts_created

    # ----------------------------------------------------------------
    # PRIVATE
    # ----------------------------------------------------------------

    async def _get_baseline(
        self,
        facility_id: UUID,
        energy_source_id: UUID,
        target_time: datetime,
        baseline_start: datetime,
        baseline_end: datetime,
    ) -> float | None:
        """
        Aynı saat-dakika dilimi için geçmiş verilerin ortalamasını alır.
        Örnek: 14:30'daki tüketim için, geçmiş 7 günün 14:30 değerlerinin ortalaması.
        """
        # Aynı saat ve dakikaya denk gelen kayıtlar (21:00-21:59 gibi)
        hour_start = target_time.replace(minute=0, second=0, microsecond=0)
        hour_end = hour_start + timedelta(hours=1)

        q = (
            select(func.avg(EnergyConsumption.consumption_value))
            .where(
                EnergyConsumption.facility_id == facility_id,
                EnergyConsumption.energy_source_id == energy_source_id,
                EnergyConsumption.recorded_at >= baseline_start,
                EnergyConsumption.recorded_at < baseline_end,
                # Aynı saat dilimi
                func.extract("hour", EnergyConsumption.recorded_at)
                == target_time.hour,
            )
        )
        result = await self.db.execute(q)
        avg = result.scalar_one()
        return float(avg) if avg is not None else None

    async def _has_recent_alert(
        self,
        facility_id: UUID,
        energy_source_id: UUID,
        hours_window: int = 6,
    ) -> bool:
        """Aynı kaynak için son N saatte otomatik uyarı var mı? (deduplication)"""
        since = datetime.now(timezone.utc) - timedelta(hours=hours_window)
        q = select(func.count(Alert.id)).where(
            Alert.facility_id == facility_id,
            Alert.energy_source_id == energy_source_id,
            Alert.is_auto_generated == True,
            Alert.detected_at >= since,
        )
        count = (await self.db.execute(q)).scalar_one()
        return count > 0

    @staticmethod
    def _classify_severity(deviation_pct: float) -> str:
        """Sapma yüzdesine göre severity belirler."""
        abs_dev = abs(deviation_pct)
        if abs_dev > 100:
            return "critical"
        elif abs_dev > 50:
            return "high"
        elif abs_dev > 30:
            return "medium"
        return "low"

    @staticmethod
    def _get_recommendation(severity: str) -> str:
        """Severity'e göre öneri metni."""
        recs = {
            "critical": (
                "Tüketimde kritik seviyede anomali tespit edildi. "
                "Ekipman arızası veya kaçak olma ihtimaline karşı "
                "tesisi acilen kontrol edin."
            ),
            "high": (
                "Tüketim normalin çok üzerinde. Enerji kaynağını ve "
                "bağlı ekipmanları gözden geçirin."
            ),
            "medium": (
                "Tüketim normalin üzerinde. Çalışma saatlerini ve "
                "ekipman verimliliğini kontrol etmeniz önerilir."
            ),
            "low": (
                "Hafif sapma tespit edildi. İzlemeye devam edin."
            ),
        }
        return recs.get(severity, "")

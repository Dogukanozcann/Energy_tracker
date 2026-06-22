"""
CSV/Excel toplu veri import servisi.
Enerji tüketim kayıtlarını dosyadan okur ve veritabanına ekler.
"""

import csv
import io
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.energy_consumption import EnergyConsumption
from app.models.energy_source import EnergySource


class ImportResult:
    def __init__(self):
        self.created: int = 0
        self.skipped: int = 0
        self.errors: list[str] = []


class ImportService:
    """Toplu veri import işlemleri."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def import_consumption_csv(
        self,
        facility_id: UUID,
        content: str,
        source_map: dict[str, UUID] | None = None,
    ) -> ImportResult:
        """CSV içeriğini parse eder ve enerji tüketim kaydı olarak ekler.
        
        Beklenen CSV sütunları: recorded_at, consumption_value, unit, source, cost (opsiyonel)
        """
        result = ImportResult()
        reader = csv.DictReader(io.StringIO(content))

        # Varsayılan energy_source_id bul
        if not source_map:
            src_result = await self.db.execute(
                select(EnergySource).limit(1)
            )
            src = src_result.scalar_one_or_none()
            if src is None:
                result.errors.append("Hiç enerji kaynağı tanımlı değil.")
                return result
            source_map = {}

        for row_num, row in enumerate(reader, start=2):
            try:
                recorded_at_str = row.get("recorded_at") or row.get("tarih")
                value_str = row.get("consumption_value") or row.get("deger") or row.get("value")
                unit = row.get("unit") or row.get("birim") or "kWh"
                source_label = row.get("source") or row.get("kaynak") or "manual"
                cost_str = row.get("cost") or row.get("maliyet")
                consumption_type = row.get("consumption_type") or row.get("tip") or "consumption"
                notes = row.get("notes") or row.get("notlar") or None

                if not recorded_at_str or not value_str:
                    result.skipped += 1
                    continue

                recorded_at = datetime.fromisoformat(recorded_at_str)
                value = float(value_str.replace(",", "."))
                cost = float(cost_str.replace(",", ".")) if cost_str else None

                # Energy source ID bul / oluştur
                source_id = source_map.get(source_label)
                if source_id is None:
                    src_result = await self.db.execute(
                        select(EnergySource).where(
                            EnergySource.name == source_label
                        ).limit(1)
                    )
                    src = src_result.scalar_one_or_none()
                    if src:
                        source_id = src.id
                    else:
                        # Varsayılan source kullan
                        src_result = await self.db.execute(
                            select(EnergySource).limit(1)
                        )
                        src = src_result.scalar_one_or_none()
                        source_id = src.id if src else None

                if source_id is None:
                    result.errors.append(f"Satır {row_num}: Enerji kaynağı bulunamadı.")
                    continue

                record = EnergyConsumption(
                    facility_id=facility_id,
                    energy_source_id=source_id,
                    recorded_at=recorded_at,
                    consumption_value=value,
                    unit=unit,
                    cost=cost,
                    consumption_type=consumption_type,
                    notes=notes,
                    source=f"import:{source_label}",
                    is_estimated=False,
                )
                self.db.add(record)
                result.created += 1

            except Exception as e:
                result.errors.append(f"Satır {row_num}: {e!s}")

        if result.created > 0:
            await self.db.flush()

        return result

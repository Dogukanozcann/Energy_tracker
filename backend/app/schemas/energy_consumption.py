from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ----- Request -----

class EnergyConsumptionCreate(BaseModel):
    facility_id: UUID
    energy_source_id: UUID
    recorded_at: datetime
    period_start: datetime | None = None
    period_end: datetime | None = None
    consumption_value: float = Field(..., gt=0)
    unit: str = "kWh"
    cost: float | None = None
    source: str = "manual"
    is_estimated: bool = False
    notes: str | None = None
    external_id: str | None = None


class EnergyConsumptionBatchCreate(BaseModel):
    items: list[EnergyConsumptionCreate] = Field(..., min_length=1, max_length=5000)


class EnergyConsumptionFilterParams(BaseModel):
    """Query parametreleri — doğrudan schema değil, endpoint'te kullanılır."""
    facility_id: UUID
    energy_source_id: UUID | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    skip: int = 0
    limit: int = 100


# ----- Response -----

class EnergyConsumptionResponse(BaseModel):
    id: UUID
    facility_id: UUID
    energy_source_id: UUID
    recorded_at: datetime
    period_start: datetime | None
    period_end: datetime | None
    consumption_value: float
    unit: str
    cost: float | None
    source: str
    is_estimated: bool
    notes: str | None
    external_id: str | None
    created_at: datetime

    # İlişkili alan (opsiyonel, sorguda join yapılırsa doldurulur)
    energy_source_name: str | None = None

    model_config = {"from_attributes": True}


class EnergyConsumptionListResponse(BaseModel):
    items: list[EnergyConsumptionResponse]
    total: int
    total_value: float | None = None          # Toplam tüketim (opsiyonel aggregasyon)
    total_cost: float | None = None           # Toplam maliyet


class BatchImportResponse(BaseModel):
    created: int
    skipped: int
    errors: list[str]
    message: str

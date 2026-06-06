from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ----- Request -----

class CarbonCalculateRequest(BaseModel):
    """Tek bir tüketim kaydı için karbon hesaplama talebi."""
    consumption_id: UUID
    force_recalculate: bool = False  # True = mevcut kayıt varsa üzerine yaz


class CarbonBatchCalculateRequest(BaseModel):
    """Toplu karbon hesaplama talebi."""
    facility_id: UUID
    date_from: datetime | None = None
    date_to: datetime | None = None
    force_recalculate: bool = False


class FootprintGenerateRequest(BaseModel):
    """Periyodik karbon özeti oluşturma talebi."""
    facility_id: UUID
    year: int = Field(..., ge=2020, le=2100)
    month: int | None = Field(None, ge=1, le=12)


# ----- Response -----

class CarbonFootprintItemResponse(BaseModel):
    id: UUID
    energy_consumption_id: UUID
    energy_source_id: UUID
    scope: str
    consumption_amount: float
    consumption_unit: str
    co2_factor_used: float
    calculated_co2_kg: float
    factor_source: str | None
    calculated_at: datetime

    model_config = {"from_attributes": True}


class CarbonFootprintItemListResponse(BaseModel):
    items: list[CarbonFootprintItemResponse]
    total: int
    total_co2_kg: float | None


class CarbonFootprintResponse(BaseModel):
    id: UUID
    facility_id: UUID
    calculation_start: date
    calculation_end: date
    calculation_year: int
    calculation_month: int | None
    calculation_quarter: int | None
    total_co2_kg: float
    scope_1_co2_kg: float | None
    scope_2_co2_kg: float | None
    scope_3_co2_kg: float | None
    intensity_per_area: float | None
    methodology: str
    status: str
    calculated_at: datetime | None
    confirmed_at: datetime | None

    model_config = {"from_attributes": True}


class CarbonFootprintListResponse(BaseModel):
    items: list[CarbonFootprintResponse]
    total: int


class BatchCalculateResponse(BaseModel):
    processed: int
    total_co2_kg: float
    message: str

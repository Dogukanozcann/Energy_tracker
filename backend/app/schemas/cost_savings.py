from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ProductionSavingsItem(BaseModel):
    id: UUID
    facility_id: UUID
    energy_source_id: UUID
    energy_source_name: str
    recorded_at: datetime
    consumption_value: float
    unit: str
    savings_amount: float
    co2_avoided_kg: float
    tree_equivalent: float

    model_config = {"from_attributes": True}


class ProductionSavingsListResponse(BaseModel):
    items: list[ProductionSavingsItem]
    total: int
    total_savings: float
    total_co2_avoided: float
    total_tree_equivalent: float


class SavingsSummaryResponse(BaseModel):
    total_production: float
    total_savings: float
    total_co2_avoided: float
    total_tree_equivalent: float
    source_breakdown: list[dict]


class DailyComparisonItem(BaseModel):
    date: str
    production_value: float
    savings_amount: float
    co2_avoided_kg: float
    tree_equivalent: float


class DailyComparisonResponse(BaseModel):
    items: list[DailyComparisonItem]

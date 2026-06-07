from uuid import UUID

from pydantic import BaseModel


class SourceComparison(BaseModel):
    energy_source_id: UUID
    energy_source_name: str
    current_week_value: float
    previous_week_value: float
    change_pct: float
    unit: str


class WeeklyComparisonResponse(BaseModel):
    facility_id: UUID
    current_week_label: str
    previous_week_label: str
    current_week_total: float
    previous_week_total: float
    total_change_pct: float
    sources: list[SourceComparison]


class SourceComparisonDetail(BaseModel):
    energy_source_id: UUID
    energy_source_name: str
    current_week_value: float
    previous_week_value: float
    change_pct: float
    unit: str
    created_alerts: int = 0


class WeeklyAlertResponse(BaseModel):
    compared: WeeklyComparisonResponse
    alerts_created: int
    source_details: list[SourceComparisonDetail]

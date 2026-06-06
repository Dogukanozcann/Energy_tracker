from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ----- Request -----

class AlertCreate(BaseModel):
    """Manuel uyarı oluşturma."""
    facility_id: UUID
    energy_consumption_id: UUID | None = None
    energy_source_id: UUID | None = None
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    severity: str = "medium"
    category: str = "anomaly"
    detected_value: float | None = None
    expected_value: float | None = None
    threshold_value: float | None = None
    deviation_percent: float | None = None
    recommendation_text: str | None = None


class AlertStatusUpdate(BaseModel):
    """Uyarı durumu güncelleme (acknowledge / resolve / dismiss)."""
    status: str = Field(..., pattern=r"^(acknowledged|resolved|dismissed)$")


class DetectAnomalyRequest(BaseModel):
    """Anomali tespitini tetikleme."""
    facility_id: UUID
    energy_source_id: UUID | None = None
    # Zaman aralığı (boş = son 24 saat)
    date_from: datetime | None = None
    date_to: datetime | None = None
    # Eşik: ortalamadan % sapma (örn. 20 = %20 üzeri anomali)
    deviation_threshold: float = 20.0


# ----- Response -----

class AlertResponse(BaseModel):
    id: UUID
    facility_id: UUID
    energy_consumption_id: UUID | None
    energy_source_id: UUID | None
    title: str
    description: str | None
    severity: str
    category: str
    status: str
    detected_value: float | None
    expected_value: float | None
    threshold_value: float | None
    deviation_percent: float | None
    detected_at: datetime
    recommendation_text: str | None
    resolved_at: datetime | None
    is_auto_generated: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    items: list[AlertResponse]
    total: int

    # Özet istatistikler
    new_count: int = 0
    critical_count: int = 0


class DetectAnomalyResponse(BaseModel):
    alerts_created: int
    message: str

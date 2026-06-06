from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserPreferenceResponse(BaseModel):
    language: str = "tr"
    timezone: str = "Europe/Istanbul"
    energy_unit: str = "kWh"
    currency: str = "TRY"
    daily_digest: bool = False
    email_alerts: bool = True
    push_alerts: bool = False
    alert_categories: list[str] = ["anomaly", "threshold_breach"]
    weekly_report: bool = True
    monthly_goal_co2: float | None = None

    model_config = {"from_attributes": True}


class UserPreferenceUpdate(BaseModel):
    language: str | None = None
    timezone: str | None = None
    energy_unit: str | None = None
    currency: str | None = None
    daily_digest: bool | None = None
    email_alerts: bool | None = None
    push_alerts: bool | None = None
    alert_categories: list[str] | None = None
    weekly_report: bool | None = None
    monthly_goal_co2: float | None = None

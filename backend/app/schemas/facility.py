from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# --- Request ---

class FacilityCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    facility_type: str = "office"

    address: str | None = None
    city: str | None = None
    district: str | None = None
    postal_code: str | None = None
    country: str = "Türkiye"

    area_sqm: float | None = None
    heated_area_sqm: float | None = None
    num_floors: int | None = None
    num_occupants: int | None = None
    operating_hours: float | None = None

    latitude: float | None = None
    longitude: float | None = None


class FacilityUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    facility_type: str | None = None
    address: str | None = None
    city: str | None = None
    district: str | None = None
    postal_code: str | None = None
    country: str | None = None
    area_sqm: float | None = None
    heated_area_sqm: float | None = None
    num_floors: int | None = None
    num_occupants: int | None = None
    operating_hours: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_active: bool | None = None


# --- Response ---

class FacilityResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: str | None
    facility_type: str
    city: str | None
    district: str | None
    country: str
    area_sqm: float | None
    num_occupants: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FacilityListResponse(BaseModel):
    items: list[FacilityResponse]
    total: int

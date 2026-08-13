"""Warehouse response schemas."""
from typing import List, Optional

from pydantic import BaseModel, Field


class CarrierScheduleResponse(BaseModel):
    """Carrier pickup schedule."""

    carrier: str
    pickup_time: str
    days: List[str]


class OperatingHoursResponse(BaseModel):
    """Warehouse operating hours."""

    open: str
    close: str


class WarehouseResponse(BaseModel):
    """Warehouse representation."""

    id: str
    name: str
    city: str
    state: str
    address: str
    is_active: bool
    carrier_schedules: List[CarrierScheduleResponse] = Field(default_factory=list)
    operating_hours: Optional[OperatingHoursResponse] = None

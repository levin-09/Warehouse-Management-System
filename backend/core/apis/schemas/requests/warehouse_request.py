"""Warehouse request schemas."""
from typing import List, Optional

from pydantic import BaseModel, Field


class CarrierScheduleCreate(BaseModel):
    """Carrier pickup schedule."""

    carrier: str
    pickup_time: str
    days: List[str] = Field(default_factory=list)


class OperatingHoursCreate(BaseModel):
    """Warehouse operating hours."""

    open: str
    close: str


class WarehouseCreate(BaseModel):
    """Payload to create a warehouse."""

    name: str
    city: str
    state: str
    address: str
    is_active: bool = True
    carrier_schedules: List[CarrierScheduleCreate] = Field(default_factory=list)
    operating_hours: Optional[OperatingHoursCreate] = None


class WarehouseUpdate(BaseModel):
    """Payload to update a warehouse."""

    name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None
    carrier_schedules: Optional[List[CarrierScheduleCreate]] = None
    operating_hours: Optional[OperatingHoursCreate] = None

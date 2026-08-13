"""Warehouse model — physical warehouse locations."""
from typing import List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field

COLLECTION = "warehouses"


class CarrierSchedule(BaseModel):
    """Recurring pickup schedule for a carrier at a warehouse."""

    carrier: str
    pickup_time: str
    days: List[str]


class OperatingHours(BaseModel):
    """Daily operating hours for a warehouse."""

    open: str
    close: str


class Warehouse(BaseModel):
    """A physical warehouse location."""

    id: Optional[ObjectId] = Field(default=None, alias="_id")
    name: str
    city: str
    state: str
    address: str
    is_active: bool = True
    carrier_schedules: List[CarrierSchedule] = Field(default_factory=list)
    operating_hours: Optional[OperatingHours] = None

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

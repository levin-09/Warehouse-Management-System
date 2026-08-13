"""Bin location request schemas."""
from typing import Optional

from pydantic import BaseModel, Field


class BinLocationCreate(BaseModel):
    """Payload to create a bin location."""

    warehouse_id: str
    bin_code: str
    aisle: str
    row: str
    shelf: str
    bin: str
    product_id: Optional[str] = None
    max_capacity: int = 100
    current_units: int = 0
    is_occupied: bool = False


class BinLocationUpdate(BaseModel):
    """Payload to update a bin location."""

    product_id: Optional[str] = None
    max_capacity: Optional[int] = None
    current_units: Optional[int] = None
    is_occupied: Optional[bool] = None

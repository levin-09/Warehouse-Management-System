"""Bin location response schemas."""
from typing import Optional

from pydantic import BaseModel


class BinLocationResponse(BaseModel):
    """Bin location representation."""

    id: str
    warehouse_id: str
    bin_code: str
    aisle: str
    row: str
    shelf: str
    bin: str
    product_id: Optional[str] = None
    max_capacity: int
    current_units: int
    is_occupied: bool

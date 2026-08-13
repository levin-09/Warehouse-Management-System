"""Bin location model — maps every physical storage spot to a product."""
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field

COLLECTION = "bin_locations"


class BinLocation(BaseModel):
    """A physical storage location mapped to a product."""

    id: Optional[ObjectId] = Field(default=None, alias="_id")
    warehouse_id: ObjectId
    bin_code: str
    aisle: str
    row: str
    shelf: str
    bin: str
    product_id: Optional[ObjectId] = None
    max_capacity: int = 100
    current_units: int = 0
    is_occupied: bool = False
    last_updated: str = ""

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

"""Inventory model — real-time stock levels per product per warehouse.

Invariant (enforced at the application layer): ``quantity_available`` always equals
``quantity_good`` minus ``quantity_reserved``.
"""
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field

COLLECTION = "inventory"


class Inventory(BaseModel):
    """Stock level for a product at a warehouse."""

    id: Optional[ObjectId] = Field(default=None, alias="_id")
    product_id: ObjectId
    warehouse_id: ObjectId
    seller_id: ObjectId
    quantity_good: int = 0
    quantity_damaged: int = 0
    quantity_reserved: int = 0
    quantity_available: int = 0
    bin_location: str = ""
    last_updated: str = ""
    last_updated_by: Optional[ObjectId] = None

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

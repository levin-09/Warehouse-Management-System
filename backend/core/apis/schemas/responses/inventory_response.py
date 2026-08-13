"""Inventory response schemas."""
from typing import Optional

from pydantic import BaseModel


class InventoryResponse(BaseModel):
    """Inventory representation."""

    id: str
    product_id: str
    warehouse_id: str
    seller_id: str
    quantity_good: int
    quantity_damaged: int
    quantity_reserved: int
    quantity_available: int
    bin_location: str
    last_updated: str
    last_updated_by: Optional[str] = None


class StockLevelResponse(BaseModel):
    """Live stock level for a product."""

    product_id: str
    product_name: str
    upc_barcode: str
    warehouse_id: str
    quantity_good: int
    quantity_damaged: int
    quantity_reserved: int
    quantity_available: int
    bin_location: str

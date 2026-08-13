"""Inventory request schemas."""
from typing import Optional

from pydantic import BaseModel, Field


class InventoryAdjustRequest(BaseModel):
    """Payload to adjust inventory stock counts.

    ``quantity_good`` is the intended new good-stock count; reserved is preserved
    and available is recomputed as good minus reserved.
    """

    quantity_good: Optional[int] = None
    quantity_damaged: Optional[int] = None
    bin_location: Optional[str] = None


class ReserveStockRequest(BaseModel):
    """Payload to reserve stock for an order.

    Uses an atomic conditional decrement so concurrent reservations cannot
    oversell available stock.
    """

    product_id: str
    warehouse_id: str
    quantity: int = Field(..., ge=1)

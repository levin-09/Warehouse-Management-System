"""Order response schemas."""
from typing import List, Optional

from pydantic import BaseModel

from core.models.enums import OrderStatus


class OrderItemResponse(BaseModel):
    """A line item on an order."""

    product_id: str
    upc_barcode: str
    product_name: str
    quantity: int


class CustomerResponse(BaseModel):
    """Order customer details."""

    name: str
    address: str


class ShippingResponse(BaseModel):
    """Shipping details."""

    carrier: str
    tracking_number: str
    weight_lbs: float
    ship_cost: float
    shipped_at: Optional[str] = None


class OrderResponse(BaseModel):
    """Order representation."""

    id: str
    order_ref: str
    seller_id: str
    warehouse_id: str
    customer: CustomerResponse
    status: OrderStatus
    assigned_to: Optional[str] = None
    items: List[OrderItemResponse]
    shipping: Optional[ShippingResponse] = None

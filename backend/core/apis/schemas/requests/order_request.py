"""Order request schemas."""
from typing import List, Optional

from pydantic import BaseModel, Field

from core.models.enums import OrderStatus


class OrderItemCreate(BaseModel):
    """A line item on an order."""

    product_id: str
    quantity: int = Field(..., ge=1)


class CustomerCreate(BaseModel):
    """Order customer details."""

    name: str
    address: str


class OrderCreate(BaseModel):
    """Payload to create a new order."""

    order_ref: str
    seller_id: str
    warehouse_id: str
    customer: CustomerCreate
    items: List[OrderItemCreate] = Field(default_factory=list)
    assigned_to: Optional[str] = None


class OrderStatusUpdate(BaseModel):
    """Payload to update order status and optional shipping details."""

    status: OrderStatus
    shipping: Optional[dict] = None

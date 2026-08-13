"""Order model — outbound customer orders with embedded items."""
from typing import List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from core.models.enums import OrderStatus

COLLECTION = "orders"


class OrderItem(BaseModel):
    """A line item embedded in an order document."""

    product_id: ObjectId
    upc_barcode: str
    product_name: str
    quantity: int


class Customer(BaseModel):
    """Customer shipping/billing details for an order."""

    name: str
    address: str


class BoxDimensions(BaseModel):
    """Shipment box dimensions."""

    length_in: float
    width_in: float
    height_in: float


class Shipping(BaseModel):
    """Shipping details for a shipped order."""

    carrier: str = ""
    tracking_number: str = ""
    weight_lbs: float = 0.0
    box_dimensions: Optional[BoxDimensions] = None
    ship_cost: float = 0.0
    shipped_at: Optional[str] = None


class Order(BaseModel):
    """An outbound customer order."""

    id: Optional[ObjectId] = Field(default=None, alias="_id")
    order_ref: str
    seller_id: ObjectId
    warehouse_id: ObjectId
    customer: Customer
    status: OrderStatus = OrderStatus.PENDING
    assigned_to: Optional[ObjectId] = None
    items: List[OrderItem] = Field(default_factory=list)
    shipping: Optional[Shipping] = None

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

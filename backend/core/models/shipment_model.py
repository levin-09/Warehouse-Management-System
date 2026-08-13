"""Shipment model — inbound deliveries with embedded line items."""
from typing import List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from core.models.enums import DamageGrade, ShipmentStatus

COLLECTION = "shipments"


class ShipmentItem(BaseModel):
    """A line item embedded in a shipment document."""

    product_id: ObjectId
    upc_barcode: str
    product_name: str
    quantity_expected: int
    quantity_received: int = 0
    quantity_damaged: int = 0
    damage_grade: Optional[DamageGrade] = None
    damage_notes: str = ""


class Shipment(BaseModel):
    """An inbound delivery with its line items embedded."""

    id: Optional[ObjectId] = Field(default=None, alias="_id")
    shipment_ref: str
    seller_id: ObjectId
    warehouse_id: ObjectId
    carrier: str = ""
    status: ShipmentStatus = ShipmentStatus.DRAFT
    received_by: Optional[ObjectId] = None
    received_at: Optional[str] = None
    notes: str = ""
    items: List[ShipmentItem] = Field(default_factory=list)

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

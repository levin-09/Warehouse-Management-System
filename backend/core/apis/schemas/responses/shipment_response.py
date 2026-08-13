"""Shipment response schemas."""
from typing import List, Optional

from pydantic import BaseModel

from core.models.enums import DamageGrade, ShipmentStatus


class ShipmentItemResponse(BaseModel):
    """A line item on a shipment."""

    product_id: str
    upc_barcode: str
    product_name: str
    quantity_expected: int
    quantity_received: int
    quantity_damaged: int
    damage_grade: Optional[DamageGrade] = None
    damage_notes: str = ""


class ShipmentResponse(BaseModel):
    """Shipment representation."""

    id: str
    shipment_ref: str
    seller_id: str
    warehouse_id: str
    carrier: str
    status: ShipmentStatus
    received_by: Optional[str] = None
    received_at: Optional[str] = None
    notes: str
    items: List[ShipmentItemResponse]

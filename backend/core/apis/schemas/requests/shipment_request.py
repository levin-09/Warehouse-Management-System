"""Shipment request schemas."""
from typing import List, Optional

from pydantic import BaseModel, Field

from core.models.enums import DamageGrade


class ShipmentItemCreate(BaseModel):
    """A line item on a shipment."""

    product_id: str
    quantity_expected: int = Field(..., ge=0)
    quantity_received: int = 0
    quantity_damaged: int = 0
    damage_grade: Optional[DamageGrade] = None
    damage_notes: str = ""


class ShipmentDraftCreate(BaseModel):
    """Payload to create a draft shipment (verify + scan items)."""

    shipment_ref: str
    seller_id: str
    warehouse_id: str
    carrier: str = ""
    notes: str = ""
    items: List[ShipmentItemCreate] = Field(default_factory=list)


class ShipmentItemUpdate(BaseModel):
    """Update to a single line item during receiving."""

    product_id: str
    quantity_received: int = Field(..., ge=0)
    quantity_damaged: int = Field(..., ge=0)
    damage_grade: Optional[DamageGrade] = None
    damage_notes: str = ""


class ShipmentConfirm(BaseModel):
    """Payload to confirm receipt of a shipment."""

    shipment_ref: str
    received_by: str
    items: List[ShipmentItemUpdate] = Field(default_factory=list)
    notes: str = ""

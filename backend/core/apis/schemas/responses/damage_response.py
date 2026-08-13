"""Damage record response schemas."""
from typing import Optional

from pydantic import BaseModel

from core.models.enums import DamageGrade


class DamageRecordResponse(BaseModel):
    """Damage assessment representation."""

    id: str
    shipment_id: Optional[str] = None
    shipment_ref: str
    product_id: str
    product_name: str
    seller_id: str
    warehouse_id: str
    quantity_damaged: int
    damage_grade: DamageGrade
    damage_notes: str
    carrier: str
    carrier_tracking: str
    assessed_by: Optional[str] = None
    action_taken: str
    seller_notified: bool

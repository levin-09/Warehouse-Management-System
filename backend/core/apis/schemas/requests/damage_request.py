"""Damage record request schemas."""
from typing import Optional

from pydantic import BaseModel, Field

from core.models.enums import DamageGrade


class DamageRecordCreate(BaseModel):
    """Payload to create a damage assessment."""

    shipment_id: Optional[str] = None
    shipment_ref: str = ""
    product_id: str
    warehouse_id: str
    quantity_damaged: int = Field(..., ge=1)
    damage_grade: DamageGrade
    damage_notes: str = ""
    carrier: str = ""
    carrier_tracking: str = ""
    action_taken: str = ""

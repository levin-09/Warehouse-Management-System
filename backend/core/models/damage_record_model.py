"""Damage record model — damage assessments using the grading system."""
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from core.models.enums import DamageGrade

COLLECTION = "damage_records"


class DamageRecord(BaseModel):
    """A damage assessment for damaged units."""

    id: Optional[ObjectId] = Field(default=None, alias="_id")
    shipment_id: Optional[ObjectId] = None
    shipment_ref: str = ""
    product_id: ObjectId
    product_name: str
    seller_id: ObjectId
    warehouse_id: ObjectId
    quantity_damaged: int
    damage_grade: DamageGrade
    damage_notes: str = ""
    carrier: str = ""
    carrier_tracking: str = ""
    assessed_by: Optional[ObjectId] = None
    action_taken: str = ""
    seller_notified: bool = False
    seller_notified_at: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

"""Return model — customer returns from creation to resolution."""
from typing import List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from core.models.enums import DamageGrade, ReturnAction, ReturnCondition, ReturnStatus

COLLECTION = "returns"


class ReturnItem(BaseModel):
    """A returned line item."""

    product_id: ObjectId
    product_name: str
    quantity: int
    condition: ReturnCondition
    damage_grade: Optional[DamageGrade] = None
    action_taken: Optional[ReturnAction] = None


class Return(BaseModel):
    """A customer return record."""

    id: Optional[ObjectId] = Field(default=None, alias="_id")
    return_ref: str
    original_order_id: ObjectId
    original_order_ref: str
    seller_id: ObjectId
    warehouse_id: ObjectId
    items: List[ReturnItem] = Field(default_factory=list)
    return_reason: str = ""
    status: ReturnStatus = ReturnStatus.PENDING
    processed_by: Optional[ObjectId] = None
    seller_notified: bool = False
    completed_at: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

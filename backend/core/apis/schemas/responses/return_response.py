"""Return response schemas."""
from typing import List, Optional

from pydantic import BaseModel

from core.models.enums import DamageGrade, ReturnAction, ReturnCondition, ReturnStatus


class ReturnItemResponse(BaseModel):
    """A returned line item."""

    product_id: str
    product_name: str
    quantity: int
    condition: ReturnCondition
    damage_grade: Optional[DamageGrade] = None
    action_taken: Optional[ReturnAction] = None


class ReturnResponse(BaseModel):
    """Return representation."""

    id: str
    return_ref: str
    original_order_id: str
    original_order_ref: str
    seller_id: str
    warehouse_id: str
    items: List[ReturnItemResponse]
    return_reason: str
    status: ReturnStatus
    processed_by: Optional[str] = None
    seller_notified: bool
    completed_at: Optional[str] = None

"""Return request schemas."""
from typing import List, Optional

from pydantic import BaseModel, Field

from core.models.enums import DamageGrade, ReturnAction, ReturnCondition


class ReturnItemCreate(BaseModel):
    """A returned line item."""

    product_id: str
    quantity: int = Field(..., ge=1)
    condition: ReturnCondition
    damage_grade: Optional[DamageGrade] = None
    action_taken: Optional[ReturnAction] = None


class ReturnCreate(BaseModel):
    """Payload to create/process a return."""

    original_order_id: str
    return_reason: str = ""
    items: List[ReturnItemCreate] = Field(default_factory=list)
    processed_by: str = ""

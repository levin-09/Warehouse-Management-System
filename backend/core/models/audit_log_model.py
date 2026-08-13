"""Audit log model — immutable record of every system action.

These documents are INSERT-only. The application never exposes update or delete
for this collection.
"""
from typing import Any, Dict, Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from core.models.enums import AuditMethod

COLLECTION = "audit_logs"


class AuditLog(BaseModel):
    """A single immutable audit entry."""

    id: Optional[ObjectId] = Field(default=None, alias="_id")
    user_id: Optional[ObjectId] = None
    user_name: str = "system"
    action: str
    collection_name: str
    record_id: Optional[ObjectId] = None
    warehouse_id: Optional[ObjectId] = None
    old_value: Dict[str, Any] = Field(default_factory=dict)
    new_value: Dict[str, Any] = Field(default_factory=dict)
    method: AuditMethod = AuditMethod.MANUAL_ENTRY
    ip_address: str = ""
    created_at: str = ""

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

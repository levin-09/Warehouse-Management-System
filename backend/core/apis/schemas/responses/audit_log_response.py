"""Audit log response schemas."""
from typing import Any, Dict, Optional

from pydantic import BaseModel

from core.models.enums import AuditMethod


class AuditLogResponse(BaseModel):
    """Audit log entry representation."""

    id: str
    user_id: Optional[str] = None
    user_name: str
    action: str
    collection_name: str
    record_id: Optional[str] = None
    warehouse_id: Optional[str] = None
    old_value: Dict[str, Any]
    new_value: Dict[str, Any]
    method: AuditMethod
    ip_address: str
    created_at: str

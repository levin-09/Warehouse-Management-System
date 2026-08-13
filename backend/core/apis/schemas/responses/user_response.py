"""User response schemas."""
from typing import Optional

from pydantic import BaseModel

from core.models.enums import UserRole


class UserResponse(BaseModel):
    """User representation without the password hash."""

    id: str
    full_name: str
    email: str
    role: UserRole
    warehouse_id: Optional[str] = None
    is_active: bool
    last_login: Optional[str] = None

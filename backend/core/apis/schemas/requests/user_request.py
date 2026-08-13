"""User request schemas."""
from typing import Optional

from pydantic import BaseModel, Field

from core.models.enums import UserRole


class UserCreate(BaseModel):
    """Payload to create a warehouse staff user."""

    full_name: str
    email: str
    password: str = Field(..., min_length=6)
    role: UserRole
    warehouse_id: str
    is_active: bool = True


class UserUpdate(BaseModel):
    """Payload to update a user's non-credential fields."""

    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    warehouse_id: Optional[str] = None
    is_active: Optional[bool] = None


class PasswordChange(BaseModel):
    """Payload to change a user's password."""

    old_password: str
    new_password: str = Field(..., min_length=6)

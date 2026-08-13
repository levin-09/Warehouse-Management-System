"""User model — staff accounts and roles."""
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from core.models.enums import UserRole

COLLECTION = "users"


class User(BaseModel):
    """A person who can log into the WMS."""

    id: Optional[ObjectId] = Field(default=None, alias="_id")
    full_name: str
    email: str
    password_hash: str
    role: UserRole
    warehouse_id: Optional[ObjectId] = None
    is_active: bool = True
    last_login: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

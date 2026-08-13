"""Auth request schemas."""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Credentials for user login."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")

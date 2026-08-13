"""Auth response schemas."""
from typing import Optional

from pydantic import BaseModel


class LoginResponse(BaseModel):
    """Successful login response with a JWT."""

    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str
    warehouse_id: Optional[str] = None
    full_name: str

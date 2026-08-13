"""FastAPI dependencies for authentication."""
from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from commons.auth import decode_jwt
from core.cruds.user_crud import CRUDUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Decode the bearer token and return authenticated claims.

    Rejects missing/invalid tokens with 401 and inactive users with 403.

    Args:
        token: Bearer token.

    Returns:
        dict: Authenticated user claims (id, email, role, warehouse_id, full_name).

    Raises:
        HTTPException 401: Invalid or missing token.
        HTTPException 403: User account is not active.
    """
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    # Staff endpoints are not for seller tokens. Seller-portal routes must use a
    # dedicated dependency scoped to the seller's own data.
    if payload.get("role") == "seller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller tokens cannot access staff endpoints",
        )
    user = await CRUDUser().get_by_id(id=payload.get("id"))
    if user is None or not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")
    return payload

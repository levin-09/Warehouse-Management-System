"""Seller authentication dependency.

Seller tokens are scoped to a single seller. This dependency decodes the token and
returns the seller's id so seller-portal endpoints can filter data to that seller
only, preventing a seller from reading another seller's data.
"""
from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from commons.auth import decode_jwt
from core.cruds.seller_crud import CRUDSeller

seller_oauth2 = OAuth2PasswordBearer(tokenUrl="/v1/auth/seller/login")


async def get_current_seller(token: str = Depends(seller_oauth2)) -> Dict[str, Any]:
    """Decode a seller token and return the seller identity.

    Args:
        token: Seller bearer token.

    Returns:
        dict: Seller claims with the seller's ``id``.

    Raises:
        HTTPException 401: Invalid token.
        HTTPException 403: Not a seller, or seller account inactive.
    """
    payload = decode_jwt(token)
    if not payload or payload.get("role") != "seller":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid seller credentials",
        )
    seller = await CRUDSeller().get_by_id(id=payload.get("id"))
    if seller is None or not seller.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller account is not active",
        )
    return {"seller_id": payload.get("id"), "email": payload.get("email")}

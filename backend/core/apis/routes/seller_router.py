"""Seller routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from commons.dependencies import get_current_user
from core import logger
from core.apis.schemas.requests.seller_request import SellerCreate, SellerUpdate
from core.apis.schemas.responses.seller_response import SellerResponse
from core.controllers.seller_controller import SellerController

seller_router = APIRouter(prefix="/v1/sellers", tags=["Sellers"])
logging = logger(__name__)


@seller_router.post("", response_model=SellerResponse, status_code=status.HTTP_201_CREATED)
async def create_seller(request: SellerCreate, auth: dict = Depends(get_current_user)):
    """
    Create a seller (admin only).

    Args:
        request (SellerCreate): Seller payload.
        auth (dict): Authenticated user claims.

    Returns:
        SellerResponse: Created seller.
    """
    try:
        logging.info("Calling POST /v1/sellers endpoint")
        response = await SellerController().create(request.model_dump(), auth)
        return SellerResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in POST /v1/sellers endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in POST /v1/sellers endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@seller_router.get("", response_model=list[SellerResponse])
async def list_sellers(is_active: Optional[bool] = Query(default=None), auth: dict = Depends(get_current_user)):
    """
    List sellers.

    Args:
        is_active (Optional[bool]): Active filter.
        auth (dict): Authenticated user claims.

    Returns:
        list[SellerResponse]: Sellers.
    """
    try:
        logging.info("Calling GET /v1/sellers endpoint")
        response = await SellerController().list(auth, is_active)
        return [SellerResponse(**s) for s in response]
    except HTTPException as error:
        logging.error(f"Error in GET /v1/sellers endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/sellers endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@seller_router.get("/{seller_id}", response_model=SellerResponse)
async def get_seller(seller_id: str, auth: dict = Depends(get_current_user)):
    """
    Fetch a seller by id.

    Args:
        seller_id (str): Seller id.
        auth (dict): Authenticated user claims.

    Returns:
        SellerResponse: Seller.
    """
    try:
        logging.info(f"Calling GET /v1/sellers/{seller_id} endpoint")
        response = await SellerController().get(seller_id, auth)
        return SellerResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in GET /v1/sellers/{seller_id} endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/sellers/{seller_id} endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@seller_router.patch("/{seller_id}", response_model=SellerResponse)
async def update_seller(seller_id: str, request: SellerUpdate, auth: dict = Depends(get_current_user)):
    """
    Update a seller (admin only).

    Args:
        seller_id (str): Seller id.
        request (SellerUpdate): Update payload.
        auth (dict): Authenticated user claims.

    Returns:
        SellerResponse: Updated seller.
    """
    try:
        logging.info(f"Calling PATCH /v1/sellers/{seller_id} endpoint")
        response = await SellerController().update(seller_id, request.model_dump(), auth)
        return SellerResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in PATCH /v1/sellers/{seller_id} endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in PATCH /v1/sellers/{seller_id} endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

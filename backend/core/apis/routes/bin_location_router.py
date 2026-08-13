"""Bin location routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from commons.dependencies import get_current_user
from core import logger
from core.apis.schemas.requests.bin_location_request import BinLocationCreate, BinLocationUpdate
from core.apis.schemas.responses.bin_location_response import BinLocationResponse
from core.controllers.bin_location_controller import BinLocationController

bin_location_router = APIRouter(prefix="/v1/bin-locations", tags=["Bin Locations"])
logging = logger(__name__)


@bin_location_router.post("", response_model=BinLocationResponse, status_code=status.HTTP_201_CREATED)
async def create_bin_location(request: BinLocationCreate, auth: dict = Depends(get_current_user)):
    """
    Create a bin location.

    Args:
        request (BinLocationCreate): Bin location payload.
        auth (dict): Authenticated user claims.

    Returns:
        BinLocationResponse: Created bin location.
    """
    try:
        logging.info("Calling POST /v1/bin-locations endpoint")
        response = await BinLocationController().create(request.model_dump(), auth)
        return BinLocationResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in POST /v1/bin-locations endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in POST /v1/bin-locations endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@bin_location_router.get("", response_model=list[BinLocationResponse])
async def list_bin_locations(
    warehouse_id: Optional[str] = Query(default=None),
    empty: bool = Query(default=False),
    auth: dict = Depends(get_current_user),
):
    """
    List bin locations.

    Args:
        warehouse_id (Optional[str]): Warehouse filter.
        empty (bool): Only empty bins.
        auth (dict): Authenticated user claims.

    Returns:
        list[BinLocationResponse]: Bin locations.
    """
    try:
        logging.info("Calling GET /v1/bin-locations endpoint")
        response = await BinLocationController().list(auth, warehouse_id or "", empty)
        return [BinLocationResponse(**b) for b in response]
    except HTTPException as error:
        logging.error(f"Error in GET /v1/bin-locations endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/bin-locations endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@bin_location_router.get("/product/{product_id}", response_model=BinLocationResponse)
async def find_bin_for_product(
    product_id: str, warehouse_id: str = Query(...), auth: dict = Depends(get_current_user)
):
    """
    Find the bin where a product is stored.

    Args:
        product_id (str): Product id.
        warehouse_id (str): Warehouse id.
        auth (dict): Authenticated user claims.

    Returns:
        BinLocationResponse: Bin location.
    """
    try:
        logging.info(f"Calling GET /v1/bin-locations/product/{product_id} endpoint")
        response = await BinLocationController().find_for_product(product_id, warehouse_id, auth)
        return BinLocationResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in GET /v1/bin-locations/product/{product_id} endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/bin-locations/product/{product_id} endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@bin_location_router.patch("/{bin_id}", response_model=BinLocationResponse)
async def update_bin_location(bin_id: str, request: BinLocationUpdate, auth: dict = Depends(get_current_user)):
    """
    Update a bin location.

    Args:
        bin_id (str): Bin location id.
        request (BinLocationUpdate): Update payload.
        auth (dict): Authenticated user claims.

    Returns:
        BinLocationResponse: Updated bin location.
    """
    try:
        logging.info(f"Calling PATCH /v1/bin-locations/{bin_id} endpoint")
        response = await BinLocationController().update(bin_id, request.model_dump(exclude_none=True), auth)
        return BinLocationResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in PATCH /v1/bin-locations/{bin_id} endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in PATCH /v1/bin-locations/{bin_id} endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

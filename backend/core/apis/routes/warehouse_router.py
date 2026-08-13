"""Warehouse routes."""
from fastapi import APIRouter, Depends, HTTPException, status

from commons.dependencies import get_current_user
from core import logger
from core.apis.schemas.requests.warehouse_request import WarehouseCreate, WarehouseUpdate
from core.apis.schemas.responses.warehouse_response import WarehouseResponse
from core.controllers.warehouse_controller import WarehouseController

warehouse_router = APIRouter(prefix="/v1/warehouses", tags=["Warehouses"])
logging = logger(__name__)


@warehouse_router.post("", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
async def create_warehouse(request: WarehouseCreate, auth: dict = Depends(get_current_user)):
    """
    Create a warehouse (admin only).

    Args:
        request (WarehouseCreate): Warehouse payload.
        auth (dict): Authenticated user claims.

    Returns:
        WarehouseResponse: Created warehouse.
    """
    try:
        logging.info("Calling POST /v1/warehouses endpoint")
        response = await WarehouseController().create(request.model_dump(), auth)
        return WarehouseResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in POST /v1/warehouses endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in POST /v1/warehouses endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@warehouse_router.get("", response_model=list[WarehouseResponse])
async def list_warehouses(auth: dict = Depends(get_current_user)):
    """
    List warehouses.

    Args:
        auth (dict): Authenticated user claims.

    Returns:
        list[WarehouseResponse]: Warehouses.
    """
    try:
        logging.info("Calling GET /v1/warehouses endpoint")
        response = await WarehouseController().list(auth)
        return [WarehouseResponse(**w) for w in response]
    except HTTPException as error:
        logging.error(f"Error in GET /v1/warehouses endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/warehouses endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@warehouse_router.get("/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(warehouse_id: str, auth: dict = Depends(get_current_user)):
    """
    Fetch a warehouse by id.

    Args:
        warehouse_id (str): Warehouse id.
        auth (dict): Authenticated user claims.

    Returns:
        WarehouseResponse: Warehouse.
    """
    try:
        logging.info(f"Calling GET /v1/warehouses/{warehouse_id} endpoint")
        response = await WarehouseController().get(warehouse_id, auth)
        return WarehouseResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in GET /v1/warehouses/{warehouse_id} endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/warehouses/{warehouse_id} endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@warehouse_router.patch("/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(warehouse_id: str, request: WarehouseUpdate, auth: dict = Depends(get_current_user)):
    """
    Update a warehouse (admin only).

    Args:
        warehouse_id (str): Warehouse id.
        request (WarehouseUpdate): Update payload.
        auth (dict): Authenticated user claims.

    Returns:
        WarehouseResponse: Updated warehouse.
    """
    try:
        logging.info(f"Calling PATCH /v1/warehouses/{warehouse_id} endpoint")
        response = await WarehouseController().update(warehouse_id, request.model_dump(), auth)
        return WarehouseResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in PATCH /v1/warehouses/{warehouse_id} endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in PATCH /v1/warehouses/{warehouse_id} endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

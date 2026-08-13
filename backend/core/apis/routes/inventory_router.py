"""Inventory routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from commons.dependencies import get_current_user
from core import logger
from core.apis.schemas.requests.inventory_request import InventoryAdjustRequest
from core.apis.schemas.responses.inventory_response import InventoryResponse, StockLevelResponse
from core.controllers.inventory_controller import InventoryController

inventory_router = APIRouter(prefix="/v1/inventory", tags=["Inventory"])
logging = logger(__name__)


@inventory_router.get("", response_model=list[InventoryResponse])
async def list_inventory(warehouse_id: Optional[str] = Query(default=None), auth: dict = Depends(get_current_user)):
    """
    List inventory records.

    Args:
        warehouse_id (Optional[str]): Warehouse filter.
        auth (dict): Authenticated user claims.

    Returns:
        list[InventoryResponse]: Inventory records.
    """
    try:
        logging.info("Calling GET /v1/inventory endpoint")
        response = await InventoryController().list(auth, warehouse_id or "")
        return [InventoryResponse(**i) for i in response]
    except HTTPException as error:
        logging.error(f"Error in GET /v1/inventory endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/inventory endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@inventory_router.get("/stock/{upc}", response_model=StockLevelResponse)
async def stock_by_upc(
    upc: str, warehouse_id: str = Query(...), auth: dict = Depends(get_current_user)
):
    """
    Return live stock for a product UPC at a warehouse.

    Args:
        upc (str): UPC barcode.
        warehouse_id (str): Warehouse id.
        auth (dict): Authenticated user claims.

    Returns:
        StockLevelResponse: Live stock levels.
    """
    try:
        logging.info(f"Calling GET /v1/inventory/stock/{upc} endpoint")
        response = await InventoryController().stock_by_upc(upc, warehouse_id, auth)
        return StockLevelResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in GET /v1/inventory/stock/{upc} endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/inventory/stock/{upc} endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@inventory_router.get("/low-stock", response_model=list[StockLevelResponse])
async def low_stock(warehouse_id: Optional[str] = Query(default=None), auth: dict = Depends(get_current_user)):
    """
    List low-stock products.

    Args:
        warehouse_id (Optional[str]): Warehouse filter.
        auth (dict): Authenticated user claims.

    Returns:
        list[StockLevelResponse]: Low-stock products.
    """
    try:
        logging.info("Calling GET /v1/inventory/low-stock endpoint")
        response = await InventoryController().low_stock(auth, warehouse_id or "")
        return [StockLevelResponse(**s) for s in response]
    except HTTPException as error:
        logging.error(f"Error in GET /v1/inventory/low-stock endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/inventory/low-stock endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@inventory_router.patch("/{inventory_id}", response_model=InventoryResponse)
async def adjust_inventory(
    inventory_id: str, request: InventoryAdjustRequest, auth: dict = Depends(get_current_user)
):
    """
    Adjust inventory counts (admin/manager).

    Args:
        inventory_id (str): Inventory id.
        request (InventoryAdjustRequest): Adjustment payload.
        auth (dict): Authenticated user claims.

    Returns:
        InventoryResponse: Updated inventory.
    """
    try:
        logging.info(f"Calling PATCH /v1/inventory/{inventory_id} endpoint")
        response = await InventoryController().adjust(inventory_id, request.model_dump(exclude_none=True), auth)
        return InventoryResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in PATCH /v1/inventory/{inventory_id} endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in PATCH /v1/inventory/{inventory_id} endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

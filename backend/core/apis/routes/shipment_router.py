"""Shipment routes — inbound receiving workflow."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from commons.dependencies import get_current_user
from core import logger
from core.apis.schemas.requests.shipment_request import ShipmentConfirm, ShipmentDraftCreate
from core.apis.schemas.responses.shipment_response import ShipmentResponse
from core.controllers.shipment_controller import ShipmentController

shipment_router = APIRouter(prefix="/v1/shipments", tags=["Shipments"])
logging = logger(__name__)


@shipment_router.post("/draft", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_shipment_draft(request: ShipmentDraftCreate, auth: dict = Depends(get_current_user)):
    """
    Create a draft shipment after duplicate verification.

    Args:
        request (ShipmentDraftCreate): Draft shipment payload.
        auth (dict): Authenticated user claims.

    Returns:
        ShipmentResponse: Draft shipment.

    Raises:
        HTTPException 400: Duplicate shipment reference.
    """
    try:
        logging.info("Calling POST /v1/shipments/draft endpoint")
        response = await ShipmentController().create_draft(request.model_dump(), auth)
        return ShipmentResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in POST /v1/shipments/draft endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in POST /v1/shipments/draft endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@shipment_router.post("/confirm", response_model=ShipmentResponse)
async def confirm_shipment(request: ShipmentConfirm, auth: dict = Depends(get_current_user)):
    """
    Confirm receipt of a shipment (transactional).

    Args:
        request (ShipmentConfirm): Confirmation payload.
        auth (dict): Authenticated user claims.

    Returns:
        ShipmentResponse: Confirmed shipment.
    """
    try:
        logging.info("Calling POST /v1/shipments/confirm endpoint")
        response = await ShipmentController().confirm_receipt(request.model_dump(), auth)
        return ShipmentResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in POST /v1/shipments/confirm endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in POST /v1/shipments/confirm endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@shipment_router.get("", response_model=list[ShipmentResponse])
async def list_shipments(warehouse_id: Optional[str] = Query(default=None), auth: dict = Depends(get_current_user)):
    """
    List shipments.

    Args:
        warehouse_id (Optional[str]): Warehouse filter.
        auth (dict): Authenticated user claims.

    Returns:
        list[ShipmentResponse]: Shipments.
    """
    try:
        logging.info("Calling GET /v1/shipments endpoint")
        response = await ShipmentController().list(auth, warehouse_id or "")
        return [ShipmentResponse(**s) for s in response]
    except HTTPException as error:
        logging.error(f"Error in GET /v1/shipments endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/shipments endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@shipment_router.get("/{shipment_id}", response_model=ShipmentResponse)
async def get_shipment(shipment_id: str, auth: dict = Depends(get_current_user)):
    """
    Fetch a shipment by id.

    Args:
        shipment_id (str): Shipment id.
        auth (dict): Authenticated user claims.

    Returns:
        ShipmentResponse: Shipment.
    """
    try:
        logging.info(f"Calling GET /v1/shipments/{shipment_id} endpoint")
        response = await ShipmentController().get(shipment_id, auth)
        return ShipmentResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in GET /v1/shipments/{shipment_id} endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/shipments/{shipment_id} endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

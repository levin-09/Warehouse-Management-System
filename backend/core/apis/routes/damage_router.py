"""Damage record routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from commons.dependencies import get_current_user
from core import logger
from core.apis.schemas.requests.damage_request import DamageRecordCreate
from core.apis.schemas.responses.damage_response import DamageRecordResponse
from core.controllers.damage_controller import DamageController

damage_router = APIRouter(prefix="/v1/damage-records", tags=["Damage Records"])
logging = logger(__name__)


@damage_router.post("", response_model=DamageRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_damage_record(request: DamageRecordCreate, auth: dict = Depends(get_current_user)):
    """
    Create a damage assessment record.

    Args:
        request (DamageRecordCreate): Damage record payload.
        auth (dict): Authenticated user claims.

    Returns:
        DamageRecordResponse: Created damage record.
    """
    try:
        logging.info("Calling POST /v1/damage-records endpoint")
        response = await DamageController().create(request.model_dump(), auth)
        return DamageRecordResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in POST /v1/damage-records endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in POST /v1/damage-records endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@damage_router.get("", response_model=list[DamageRecordResponse])
async def list_damage_records(
    warehouse_id: Optional[str] = Query(default=None), auth: dict = Depends(get_current_user)
):
    """
    List damage records.

    Args:
        warehouse_id (Optional[str]): Warehouse filter.
        auth (dict): Authenticated user claims.

    Returns:
        list[DamageRecordResponse]: Damage records.
    """
    try:
        logging.info("Calling GET /v1/damage-records endpoint")
        response = await DamageController().list(auth, warehouse_id or "")
        return [DamageRecordResponse(**r) for r in response]
    except HTTPException as error:
        logging.error(f"Error in GET /v1/damage-records endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/damage-records endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@damage_router.get("/{damage_id}", response_model=DamageRecordResponse)
async def get_damage_record(damage_id: str, auth: dict = Depends(get_current_user)):
    """
    Fetch a damage record by id.

    Args:
        damage_id (str): Damage record id.
        auth (dict): Authenticated user claims.

    Returns:
        DamageRecordResponse: Damage record.
    """
    try:
        logging.info(f"Calling GET /v1/damage-records/{damage_id} endpoint")
        response = await DamageController().get(damage_id, auth)
        return DamageRecordResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in GET /v1/damage-records/{damage_id} endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/damage-records/{damage_id} endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

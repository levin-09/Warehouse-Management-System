"""Return processing routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from commons.dependencies import get_current_user
from core import logger
from core.apis.schemas.requests.return_request import ReturnCreate
from core.apis.schemas.responses.return_response import ReturnResponse
from core.controllers.return_controller import ReturnController

return_router = APIRouter(prefix="/v1/returns", tags=["Returns"])
logging = logger(__name__)


@return_router.post("", response_model=ReturnResponse, status_code=status.HTTP_201_CREATED)
async def process_return(request: ReturnCreate, auth: dict = Depends(get_current_user)):
    """
    Process a customer return and apply disposition.

    Args:
        request (ReturnCreate): Return processing payload.
        auth (dict): Authenticated user claims.

    Returns:
        ReturnResponse: Created return.
    """
    try:
        logging.info("Calling POST /v1/returns endpoint")
        response = await ReturnController().process(request.model_dump(), auth)
        return ReturnResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in POST /v1/returns endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in POST /v1/returns endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@return_router.get("", response_model=list[ReturnResponse])
async def list_returns(warehouse_id: Optional[str] = Query(default=None), auth: dict = Depends(get_current_user)):
    """
    List returns.

    Args:
        warehouse_id (Optional[str]): Warehouse filter.
        auth (dict): Authenticated user claims.

    Returns:
        list[ReturnResponse]: Returns.
    """
    try:
        logging.info("Calling GET /v1/returns endpoint")
        response = await ReturnController().list(auth, warehouse_id or "")
        return [ReturnResponse(**r) for r in response]
    except HTTPException as error:
        logging.error(f"Error in GET /v1/returns endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/returns endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@return_router.get("/{return_id}", response_model=ReturnResponse)
async def get_return(return_id: str, auth: dict = Depends(get_current_user)):
    """
    Fetch a return by id.

    Args:
        return_id (str): Return id.
        auth (dict): Authenticated user claims.

    Returns:
        ReturnResponse: Return.
    """
    try:
        logging.info(f"Calling GET /v1/returns/{return_id} endpoint")
        response = await ReturnController().get(return_id, auth)
        return ReturnResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in GET /v1/returns/{return_id} endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/returns/{return_id} endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

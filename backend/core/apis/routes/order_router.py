"""Order routes — outbound order workflow."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from commons.dependencies import get_current_user
from core import logger
from core.apis.schemas.requests.order_request import OrderCreate, OrderStatusUpdate
from core.apis.schemas.responses.order_response import OrderResponse
from core.controllers.order_controller import OrderController

order_router = APIRouter(prefix="/v1/orders", tags=["Orders"])
logging = logger(__name__)


@order_router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(request: OrderCreate, auth: dict = Depends(get_current_user)):
    """
    Create an order and reserve stock for its items.

    Args:
        request (OrderCreate): Order payload.
        auth (dict): Authenticated user claims.

    Returns:
        OrderResponse: Created order.

    Raises:
        HTTPException 409: Insufficient stock.
    """
    try:
        logging.info("Calling POST /v1/orders endpoint")
        response = await OrderController().create_order(request.model_dump(), auth)
        return OrderResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in POST /v1/orders endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in POST /v1/orders endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@order_router.get("", response_model=list[OrderResponse])
async def list_orders(
    warehouse_id: Optional[str] = Query(default=None),
    assigned: bool = Query(default=False),
    auth: dict = Depends(get_current_user),
):
    """
    List orders.

    Args:
        warehouse_id (Optional[str]): Warehouse filter.
        assigned (bool): Only the caller's assigned orders.
        auth (dict): Authenticated user claims.

    Returns:
        list[OrderResponse]: Orders.
    """
    try:
        logging.info("Calling GET /v1/orders endpoint")
        response = await OrderController().list(auth, warehouse_id or "", assigned)
        return [OrderResponse(**o) for o in response]
    except HTTPException as error:
        logging.error(f"Error in GET /v1/orders endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/orders endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@order_router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, auth: dict = Depends(get_current_user)):
    """
    Fetch an order by id.

    Args:
        order_id (str): Order id.
        auth (dict): Authenticated user claims.

    Returns:
        OrderResponse: Order.
    """
    try:
        logging.info(f"Calling GET /v1/orders/{order_id} endpoint")
        response = await OrderController().get(order_id, auth)
        return OrderResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in GET /v1/orders/{order_id} endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/orders/{order_id} endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@order_router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str, request: OrderStatusUpdate, auth: dict = Depends(get_current_user)
):
    """
    Update an order's status through its workflow.

    Args:
        order_id (str): Order id.
        request (OrderStatusUpdate): Status update payload.
        auth (dict): Authenticated user claims.

    Returns:
        OrderResponse: Updated order.
    """
    try:
        logging.info(f"Calling PATCH /v1/orders/{order_id}/status endpoint")
        shipping = request.shipping if request.shipping else None
        response = await OrderController().update_status(order_id, request.status.value, auth, shipping)
        return OrderResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in PATCH /v1/orders/{order_id}/status endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in PATCH /v1/orders/{order_id}/status endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

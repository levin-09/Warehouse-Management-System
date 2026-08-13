"""Dashboard routes."""
from fastapi import APIRouter, Depends, HTTPException, status

from commons.dependencies import get_current_user
from core import logger
from core.apis.schemas.responses.dashboard_response import DashboardResponse
from core.controllers.dashboard_controller import DashboardController

dashboard_router = APIRouter(prefix="/v1/dashboard", tags=["Dashboard"])
logging = logger(__name__)


@dashboard_router.get("/overview", response_model=DashboardResponse)
async def dashboard_overview(auth: dict = Depends(get_current_user)):
    """
    Return aggregated management dashboard data (admin only).

    Args:
        auth (dict): Authenticated user claims.

    Returns:
        DashboardResponse: Dashboard overview.
    """
    try:
        logging.info("Calling GET /v1/dashboard/overview endpoint")
        response = await DashboardController().overview(auth)
        return DashboardResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in GET /v1/dashboard/overview endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/dashboard/overview endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

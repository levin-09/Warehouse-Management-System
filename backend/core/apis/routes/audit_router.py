"""Audit log routes — read-only (admin)."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from commons.dependencies import get_current_user
from core import logger
from core.apis.schemas.responses.audit_log_response import AuditLogResponse
from core.controllers.audit_log_controller import AuditLogController

audit_router = APIRouter(prefix="/v1/audit-logs", tags=["Audit Logs"])
logging = logger(__name__)


@audit_router.get("", response_model=list[AuditLogResponse])
async def list_audit_logs(
    record_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    auth: dict = Depends(get_current_user),
):
    """
    List audit log entries (admin only).

    Args:
        record_id (Optional[str]): Record id filter.
        limit (int): Max entries.
        auth (dict): Authenticated user claims.

    Returns:
        list[AuditLogResponse]: Audit entries.
    """
    try:
        logging.info("Calling GET /v1/audit-logs endpoint")
        response = await AuditLogController().list(auth, record_id or "", limit)
        return [AuditLogResponse(**a) for a in response]
    except HTTPException as error:
        logging.error(f"Error in GET /v1/audit-logs endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/audit-logs endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@audit_router.get("/history", response_model=list[AuditLogResponse])
async def audit_history(
    record_id: str = Query(...),
    collection_name: str = Query(...),
    auth: dict = Depends(get_current_user),
):
    """
    Return audit history for a specific record (admin only).

    Args:
        record_id (str): Record id.
        collection_name (str): Collection name.
        auth (dict): Authenticated user claims.

    Returns:
        list[AuditLogResponse]: Audit history.
    """
    try:
        logging.info("Calling GET /v1/audit-logs/history endpoint")
        response = await AuditLogController().history_for_record(record_id, collection_name, auth)
        return [AuditLogResponse(**a) for a in response]
    except HTTPException as error:
        logging.error(f"Error in GET /v1/audit-logs/history endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/audit-logs/history endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

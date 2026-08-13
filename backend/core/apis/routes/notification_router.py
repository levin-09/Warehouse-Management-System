"""Notification routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from commons.dependencies import get_current_user
from core import logger
from core.apis.schemas.responses.notification_response import NotificationResponse
from core.controllers.notification_controller import NotificationController

notification_router = APIRouter(prefix="/v1/notifications", tags=["Notifications"])
logging = logger(__name__)


@notification_router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(default=False), auth: dict = Depends(get_current_user)
):
    """
    List notifications for the authenticated user.

    Args:
        unread_only (bool): Only unread notifications.
        auth (dict): Authenticated user claims.

    Returns:
        list[NotificationResponse]: Notifications.
    """
    try:
        logging.info("Calling GET /v1/notifications endpoint")
        response = await NotificationController().list(auth, unread_only)
        return [NotificationResponse(**n) for n in response]
    except HTTPException as error:
        logging.error(f"Error in GET /v1/notifications endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/notifications endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@notification_router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(notification_id: str, auth: dict = Depends(get_current_user)):
    """
    Mark a notification as read.

    Args:
        notification_id (str): Notification id.
        auth (dict): Authenticated user claims.

    Returns:
        NotificationResponse: Updated notification.
    """
    try:
        logging.info(f"Calling PATCH /v1/notifications/{notification_id}/read endpoint")
        response = await NotificationController().mark_read(notification_id, auth)
        return NotificationResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in PATCH /v1/notifications/{notification_id}/read endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in PATCH /v1/notifications/{notification_id}/read endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

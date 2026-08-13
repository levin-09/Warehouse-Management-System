"""User management routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from commons.dependencies import get_current_user
from core import logger
from core.apis.schemas.requests.user_request import PasswordChange, UserCreate, UserUpdate
from core.apis.schemas.responses.user_response import UserResponse
from core.controllers.user_controller import UserController

user_router = APIRouter(prefix="/v1/users", tags=["Users"])
logging = logger(__name__)


@user_router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(request: UserCreate, auth: dict = Depends(get_current_user)):
    """
    Create a warehouse staff user (admin only).

    Args:
        request (UserCreate): User creation payload.
        auth (dict): Authenticated user claims.

    Returns:
        UserResponse: Created user.

    Raises:
        HTTPException 400/403/500.
    """
    try:
        logging.info("Calling POST /v1/users endpoint")
        response = await UserController().create_user(request.model_dump(), auth)
        return UserResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in POST /v1/users endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in POST /v1/users endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@user_router.get("", response_model=list[UserResponse])
async def list_users(role: Optional[str] = Query(default=None), auth: dict = Depends(get_current_user)):
    """
    List users.

    Args:
        role (Optional[str]): Role filter.
        auth (dict): Authenticated user claims.

    Returns:
        list[UserResponse]: List of users.
    """
    try:
        logging.info("Calling GET /v1/users endpoint")
        response = await UserController().list_users(auth, role)
        return [UserResponse(**u) for u in response]
    except HTTPException as error:
        logging.error(f"Error in GET /v1/users endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/users endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@user_router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, request: UserUpdate, auth: dict = Depends(get_current_user)):
    """
    Update a user.

    Args:
        user_id (str): Target user id.
        request (UserUpdate): Update payload.
        auth (dict): Authenticated user claims.

    Returns:
        UserResponse: Updated user.
    """
    try:
        logging.info(f"Calling PATCH /v1/users/{user_id} endpoint")
        response = await UserController().update_user(user_id, request.model_dump(), auth)
        return UserResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in PATCH /v1/users/{user_id} endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in PATCH /v1/users/{user_id} endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@user_router.delete("/{user_id}")
async def delete_user(user_id: str, auth: dict = Depends(get_current_user)):
    """
    Delete a user (admin only).

    Args:
        user_id (str): Target user id.
        auth (dict): Authenticated user claims.

    Returns:
        dict: Confirmation message.
    """
    try:
        logging.info(f"Calling DELETE /v1/users/{user_id} endpoint")
        return await UserController().delete_user(user_id, auth)
    except HTTPException as error:
        logging.error(f"Error in DELETE /v1/users/{user_id} endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in DELETE /v1/users/{user_id} endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@user_router.post("/me/password")
async def change_password(request: PasswordChange, auth: dict = Depends(get_current_user)):
    """
    Change the authenticated user's password.

    Args:
        request (PasswordChange): Old and new password.
        auth (dict): Authenticated user claims.

    Returns:
        dict: Confirmation message.
    """
    try:
        logging.info("Calling POST /v1/users/me/password endpoint")
        return await UserController().change_password(auth, request.old_password, request.new_password)
    except HTTPException as error:
        logging.error(f"Error in POST /v1/users/me/password endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in POST /v1/users/me/password endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

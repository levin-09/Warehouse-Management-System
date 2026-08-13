"""Authentication routes."""
from fastapi import APIRouter, HTTPException, status

from core import logger
from core.apis.schemas.requests.auth_request import LoginRequest
from core.apis.schemas.responses.auth_response import LoginResponse
from core.controllers.auth_controller import AuthController

auth_router = APIRouter(prefix="/v1/auth", tags=["Auth"])
logging = logger(__name__)


@auth_router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(request: LoginRequest):
    """
    Authenticate a warehouse staff user and return a JWT.

    Args:
        request (LoginRequest): Email and password.

    Returns:
        LoginResponse: Access token and user details.

    Raises:
        HTTPException 401: Invalid credentials.
        HTTPException 403: User not active.
        HTTPException 500: Internal server error.
    """
    try:
        logging.info("Calling POST /v1/auth/login endpoint")
        response = await AuthController().login(request.email, request.password)
        return LoginResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in POST /v1/auth/login endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in POST /v1/auth/login endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@auth_router.post("/seller/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def seller_login(request: LoginRequest):
    """
    Authenticate a seller and return a seller-scoped JWT.

    Args:
        request (LoginRequest): Seller portal email and password.

    Returns:
        LoginResponse: Access token and seller details.

    Raises:
        HTTPException 401: Invalid credentials.
        HTTPException 403: Seller not active.
        HTTPException 500: Internal server error.
    """
    try:
        logging.info("Calling POST /v1/auth/seller/login endpoint")
        response = await AuthController().seller_login(request.email, request.password)
        return LoginResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in POST /v1/auth/seller/login endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in POST /v1/auth/seller/login endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

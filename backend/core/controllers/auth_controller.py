"""Authentication controller."""
from fastapi import HTTPException, status

from commons.auth import create_access_token, verify_password
from core import logger
from core.cruds.seller_crud import CRUDSeller
from core.cruds.user_crud import CRUDUser

logging = logger(__name__)


class AuthController:
    """Handles user and seller login."""

    def __init__(self) -> None:
        """Initialize user and seller CRUDs."""
        self.CRUDUser = CRUDUser()
        self.CRUDSeller = CRUDSeller()

    async def login(self, email: str, password: str) -> dict:
        """Authenticate a warehouse staff user and issue a JWT.

        Args:
            email: User email.
            password: Plaintext password.

        Returns:
            dict: Login response payload with access token.

        Raises:
            HTTPException 401: Invalid credentials.
            HTTPException 403: User account is not active.
        """
        try:
            logging.info("Executing AuthController.login")
            user = await self.CRUDUser.get_by_email(email=email)
            if user is None or not verify_password(password, user.get("password_hash", "")):
                logging.warning(f"Login failed for email {email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )
            if not user.get("is_active", True):
                logging.warning(f"User {email} is not active")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is not active",
                )
            await self.CRUDUser.update_last_login(user_id=user["_id"])
            token = create_access_token(
                data={
                    "id": str(user["_id"]),
                    "email": user["email"],
                    "role": user["role"],
                    "warehouse_id": str(user.get("warehouse_id") or ""),
                    "full_name": user["full_name"],
                }
            )
            return {
                "access_token": token,
                "token_type": "bearer",
                "user_id": str(user["_id"]),
                "email": user["email"],
                "role": user["role"],
                "warehouse_id": str(user.get("warehouse_id") or ""),
                "full_name": user["full_name"],
            }
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in AuthController.login: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    async def seller_login(self, email: str, password: str) -> dict:
        """Authenticate a seller and issue a seller-scoped JWT.

        Args:
            email: Seller portal email.
            password: Plaintext password.

        Returns:
            dict: Login response payload.

        Raises:
            HTTPException 401: Invalid credentials.
            HTTPException 403: Seller account is not active.
        """
        try:
            logging.info("Executing AuthController.seller_login")
            seller = await self.CRUDSeller.get_by_email(email=email)
            portal = seller.get("portal_login") if seller else None
            if (
                seller is None
                or portal is None
                or not verify_password(password, portal.get("password_hash", ""))
            ):
                logging.warning(f"Seller login failed for {email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )
            if not seller.get("is_active", True):
                logging.warning(f"Seller {email} is not active")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Seller account is not active",
                )
            token = create_access_token(
                data={
                    "id": str(seller["_id"]),
                    "email": seller["email"],
                    "role": "seller",
                    "warehouse_id": "",
                    "full_name": seller.get("contact_name", ""),
                }
            )
            return {
                "access_token": token,
                "token_type": "bearer",
                "user_id": str(seller["_id"]),
                "email": seller["email"],
                "role": "seller",
                "warehouse_id": "",
                "full_name": seller.get("contact_name", ""),
            }
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in AuthController.seller_login: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

"""Seller controller."""
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from commons.auth import hash_password
from core import logger
from core.cruds.seller_crud import CRUDSeller
from core.models.enums import UserRole
from core.utils.rbac import require_roles

logging = logger(__name__)


class SellerController:
    """Orchestrates seller management (admin-only writes)."""

    def __init__(self) -> None:
        """Initialize the seller CRUD."""
        self.CRUDSeller = CRUDSeller()

    async def create(self, data: Dict[str, Any], auth: Dict[str, Any]) -> dict:
        """Create a seller (admin only).

        Args:
            data: Seller data.
            auth: Authenticated user.

        Returns:
            dict: Created seller payload.

        Raises:
            HTTPException 403: Not admin.
            HTTPException 400: Email or company already registered.
        """
        try:
            logging.info("Executing SellerController.create")
            require_roles(auth["role"], [UserRole.ADMIN.value])
            if await self.CRUDSeller.get_by_email(email=data["email"]):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seller email already registered")
            if await self.CRUDSeller.get_by_company(company_name=data["company_name"]):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company already registered")
            payload = dict(data)
            if data.get("portal_password"):
                payload["portal_login"] = {
                    "email": data["email"],
                    "password_hash": hash_password(data["portal_password"]),
                }
                payload.pop("portal_password")
            seller = await self.CRUDSeller.create(obj_in=payload)
            return self._format(seller)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in SellerController.create: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def list(self, auth: Dict[str, Any], is_active: Optional[bool] = None) -> List[dict]:
        """List sellers.

        Args:
            auth: Authenticated user.
            is_active: Optional active filter.

        Returns:
            List[dict]: Seller payloads.
        """
        try:
            logging.info("Executing SellerController.list")
            query: Dict[str, Any] = {}
            if is_active is not None:
                query["is_active"] = is_active
            sellers = await self.CRUDSeller.list(query=query)
            return [self._format(s) for s in sellers]
        except Exception as error:
            logging.error(f"Error in SellerController.list: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def get(self, seller_id: str, auth: Dict[str, Any]) -> dict:
        """Fetch a seller.

        Args:
            seller_id: Seller id.
            auth: Authenticated user.

        Returns:
            dict: Seller payload.

        Raises:
            HTTPException 404: Not found.
        """
        try:
            logging.info("Executing SellerController.get")
            seller = await self.CRUDSeller.get_by_id(id=seller_id)
            if seller is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")
            return self._format(seller)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in SellerController.get: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def update(self, seller_id: str, data: Dict[str, Any], auth: Dict[str, Any]) -> dict:
        """Update a seller (admin only).

        Args:
            seller_id: Seller id.
            data: Update data.
            auth: Authenticated user.

        Returns:
            dict: Updated seller payload.
        """
        try:
            logging.info("Executing SellerController.update")
            require_roles(auth["role"], [UserRole.ADMIN.value])
            seller = await self.CRUDSeller.get_by_id(id=seller_id)
            if seller is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")
            payload = {k: v for k, v in data.items() if v is not None}
            updated = await self.CRUDSeller.update(id=seller_id, update_data=payload)
            return self._format(updated)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in SellerController.update: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    @staticmethod
    def _format(s) -> dict:
        """Format a seller document for response.

        Args:
            s: Seller document.

        Returns:
            dict: Response payload.
        """
        return {
            "id": str(s["_id"]),
            "company_name": s["company_name"],
            "contact_name": s["contact_name"],
            "email": s["email"],
            "phone": s["phone"],
            "billing_rates": s.get("billing_rates", {}),
            "low_stock_threshold_default": s.get("low_stock_threshold_default", 20),
            "is_active": s.get("is_active", True),
        }

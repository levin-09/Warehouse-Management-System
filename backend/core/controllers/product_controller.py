"""Product controller."""
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import HTTPException, status

from core import logger
from core.cruds.product_crud import CRUDProduct
from core.models.enums import UserRole
from core.utils.rbac import check_read, check_write, require_roles

logging = logger(__name__)


class ProductController:
    """Orchestrates product catalog management."""

    def __init__(self) -> None:
        """Initialize the product CRUD."""
        self.CRUDProduct = CRUDProduct()

    async def create(self, data: Dict[str, Any], auth: Dict[str, Any]) -> dict:
        """Create a product (admin/manager).

        Args:
            data: Product data.
            auth: Authenticated user.

        Returns:
            dict: Created product payload.

        Raises:
            HTTPException 403: Insufficient permissions.
            HTTPException 400: UPC already exists.
        """
        try:
            logging.info("Executing ProductController.create")
            require_roles(auth["role"], [UserRole.ADMIN.value, UserRole.MANAGER.value])
            if await self.CRUDProduct.get_by_upc(upc_barcode=data["upc_barcode"]):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="UPC barcode already exists")
            payload = dict(data)
            payload["seller_id"] = ObjectId(data["seller_id"])
            product = await self.CRUDProduct.create(obj_in=payload)
            return self._format(product)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in ProductController.create: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def list(self, auth: Dict[str, Any], seller_id: Optional[str] = None) -> List[dict]:
        """List products.

        Args:
            auth: Authenticated user.
            seller_id: Optional seller filter.

        Returns:
            List[dict]: Product payloads.
        """
        try:
            logging.info("Executing ProductController.list")
            check_read(auth["role"], "products")
            query: Dict[str, Any] = {}
            if seller_id:
                query["seller_id"] = ObjectId(seller_id)
            products = await self.CRUDProduct.list(query=query)
            return [self._format(p) for p in products]
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in ProductController.list: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def get_by_upc(self, upc: str, auth: Dict[str, Any]) -> dict:
        """Fetch a product by UPC.

        Args:
            upc: UPC barcode.
            auth: Authenticated user.

        Returns:
            dict: Product payload.

        Raises:
            HTTPException 404: Not found.
        """
        try:
            logging.info("Executing ProductController.get_by_upc")
            check_read(auth["role"], "products")
            product = await self.CRUDProduct.get_by_upc(upc_barcode=upc)
            if product is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
            return self._format(product)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in ProductController.get_by_upc: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def get(self, product_id: str, auth: Dict[str, Any]) -> dict:
        """Fetch a product by id.

        Args:
            product_id: Product id.
            auth: Authenticated user.

        Returns:
            dict: Product payload.
        """
        try:
            logging.info("Executing ProductController.get")
            check_read(auth["role"], "products")
            product = await self.CRUDProduct.get_by_id(id=product_id)
            if product is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
            return self._format(product)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in ProductController.get: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def update(self, product_id: str, data: Dict[str, Any], auth: Dict[str, Any]) -> dict:
        """Update a product (admin/manager).

        Args:
            product_id: Product id.
            data: Update data.
            auth: Authenticated user.

        Returns:
            dict: Updated product payload.
        """
        try:
            logging.info("Executing ProductController.update")
            require_roles(auth["role"], [UserRole.ADMIN.value, UserRole.MANAGER.value])
            product = await self.CRUDProduct.get_by_id(id=product_id)
            if product is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
            payload = {k: v for k, v in data.items() if v is not None}
            updated = await self.CRUDProduct.update(id=product_id, update_data=payload)
            return self._format(updated)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in ProductController.update: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    @staticmethod
    def _format(p) -> dict:
        """Format a product document for response.

        Args:
            p: Product document.

        Returns:
            dict: Response payload.
        """
        return {
            "id": str(p["_id"]),
            "seller_id": str(p["seller_id"]),
            "upc_barcode": p["upc_barcode"],
            "sku": p["sku"],
            "product_name": p["product_name"],
            "description": p.get("description", ""),
            "dimensions": p.get("dimensions", {}),
            "low_stock_threshold": p.get("low_stock_threshold", 20),
            "category": p.get("category", ""),
            "is_active": p.get("is_active", True),
        }

"""Product persistence operations."""
from typing import Any, Dict, Optional

from core.cruds.base_crud import BaseCRUD


class CRUDProduct(BaseCRUD):
    """Database access layer for product records."""

    COLLECTION_NAME = "products"

    async def get_by_upc(self, *, upc_barcode: str) -> Optional[Dict[str, Any]]:
        """Fetch a product by UPC barcode.

        Args:
            upc_barcode: Product barcode.

        Returns:
            Optional[dict]: The product document, or None.
        """
        return await self.get_one(query={"upc_barcode": upc_barcode})

    async def get_by_sku(self, *, sku: str) -> Optional[Dict[str, Any]]:
        """Fetch a product by SKU.

        Args:
            sku: Product SKU.

        Returns:
            Optional[dict]: The product document, or None.
        """
        return await self.get_one(query={"sku": sku})

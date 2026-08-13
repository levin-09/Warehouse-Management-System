"""Bin location persistence operations."""
from typing import Any, Optional

from core.cruds.base_crud import BaseCRUD
from core.utils.custom.database_helper import str_to_object_id


class CRUDBinLocation(BaseCRUD):
    """Database access layer for bin locations."""

    COLLECTION_NAME = "bin_locations"

    async def get_by_product_and_warehouse(
        self, *, product_id: Any, warehouse_id: Any
    ) -> Optional[dict]:
        """Find where a product is stored at a warehouse.

        Args:
            product_id: Product id.
            warehouse_id: Warehouse id.

        Returns:
            Optional[dict]: The bin location document, or None.
        """
        return await self.get_one(
            query={
                "product_id": str_to_object_id(product_id),
                "warehouse_id": str_to_object_id(warehouse_id),
            }
        )

    async def list_empty(self, *, warehouse_id: Any) -> list:
        """List empty bins at a warehouse.

        Args:
            warehouse_id: Warehouse id.

        Returns:
            list: Empty bin location documents.
        """
        return await self.list(
            query={"warehouse_id": str_to_object_id(warehouse_id), "is_occupied": False}
        )

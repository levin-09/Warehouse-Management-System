"""Order persistence operations."""
from typing import Any, Dict, Optional

from core.cruds.base_crud import BaseCRUD


class CRUDOrder(BaseCRUD):
    """Database access layer for order records."""

    COLLECTION_NAME = "orders"

    async def get_by_ref(self, *, order_ref: str) -> Optional[Dict[str, Any]]:
        """Fetch an order by its reference number.

        Args:
            order_ref: Order reference.

        Returns:
            Optional[dict]: The order document, or None.
        """
        return await self.get_one(query={"order_ref": order_ref})

    async def update_status(self, *, id: Any, status: str, extra: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Update an order's status and optional fields.

        Args:
            id: Order document id.
            status: New order status.
            extra: Optional extra fields to set.

        Returns:
            Optional[dict]: The updated order document, or None.
        """
        update_data: Dict[str, Any] = {"status": status}
        if extra:
            update_data.update(extra)
        return await self.update(id=id, update_data=update_data)

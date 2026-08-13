"""Warehouse persistence operations."""
from typing import Any, Dict, Optional

from core.cruds.base_crud import BaseCRUD


class CRUDWarehouse(BaseCRUD):
    """Database access layer for warehouse records."""

    COLLECTION_NAME = "warehouses"

    async def get_by_name(self, *, name: str) -> Optional[Dict[str, Any]]:
        """Fetch a warehouse by name.

        Args:
            name: Warehouse name.

        Returns:
            Optional[dict]: The warehouse document, or None.
        """
        return await self.get_one(query={"name": name})

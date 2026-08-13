"""Return persistence operations."""
from typing import Any, Optional

from core.cruds.base_crud import BaseCRUD


class CRUDReturn(BaseCRUD):
    """Database access layer for return records."""

    COLLECTION_NAME = "returns"

    async def get_by_ref(self, *, return_ref: str) -> Optional[dict]:
        """Fetch a return by its reference number.

        Args:
            return_ref: Return reference.

        Returns:
            Optional[dict]: The return document, or None.
        """
        return await self.get_one(query={"return_ref": return_ref})

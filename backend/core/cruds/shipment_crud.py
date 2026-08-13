"""Shipment persistence operations."""
from typing import Any, Dict, Optional

from core.cruds.base_crud import BaseCRUD


class CRUDShipment(BaseCRUD):
    """Database access layer for shipment records."""

    COLLECTION_NAME = "shipments"

    async def get_by_ref(self, *, shipment_ref: str) -> Optional[Dict[str, Any]]:
        """Fetch a shipment by its reference/tracking number.

        Used for duplicate-entry prevention before receiving.

        Args:
            shipment_ref: Carrier tracking/reference number.

        Returns:
            Optional[dict]: The shipment document, or None if not previously received.
        """
        return await self.get_one(query={"shipment_ref": shipment_ref})

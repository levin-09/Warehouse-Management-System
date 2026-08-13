"""Bin location controller."""
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import HTTPException, status

from core import logger
from core.cruds.bin_location_crud import CRUDBinLocation
from core.models.enums import UserRole
from core.utils.rbac import check_read, require_roles

logging = logger(__name__)


class BinLocationController:
    """Orchestrates bin location management."""

    def __init__(self) -> None:
        """Initialize the bin location CRUD."""
        self.CRUDBin = CRUDBinLocation()

    async def create(self, data: Dict[str, Any], auth: Dict[str, Any]) -> dict:
        """Create a bin location (admin/manager).

        Args:
            data: Bin location data.
            auth: Authenticated user.

        Returns:
            dict: Created bin location payload.

        Raises:
            HTTPException 403: Insufficient permissions.
        """
        try:
            logging.info("Executing BinLocationController.create")
            require_roles(auth["role"], [UserRole.ADMIN.value, UserRole.MANAGER.value])
            payload = dict(data)
            payload["warehouse_id"] = ObjectId(data["warehouse_id"])
            if data.get("product_id"):
                payload["product_id"] = ObjectId(data["product_id"])
                payload["is_occupied"] = True
            bin_location = await self.CRUDBin.create(obj_in=payload)
            return self._format(bin_location)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in BinLocationController.create: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def list(self, auth: Dict[str, Any], warehouse_id: str = "", empty: bool = False) -> List[dict]:
        """List bin locations.

        Args:
            auth: Authenticated user.
            warehouse_id: Optional warehouse filter.
            empty: Only empty bins.

        Returns:
            List[dict]: Bin location payloads.
        """
        try:
            logging.info("Executing BinLocationController.list")
            check_read(auth["role"], "bin_locations")
            query: Dict[str, Any] = {}
            if warehouse_id:
                query["warehouse_id"] = ObjectId(warehouse_id)
            elif auth.get("warehouse_id"):
                query["warehouse_id"] = ObjectId(auth["warehouse_id"])
            if empty:
                query["is_occupied"] = False
            bins = await self.CRUDBin.list(query=query)
            return [self._format(b) for b in bins]
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in BinLocationController.list: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def find_for_product(self, product_id: str, warehouse_id: str, auth: Dict[str, Any]) -> dict:
        """Find the bin where a product is stored.

        Args:
            product_id: Product id.
            warehouse_id: Warehouse id.
            auth: Authenticated user.

        Returns:
            dict: Bin location payload.

        Raises:
            HTTPException 404: Not found.
        """
        try:
            logging.info("Executing BinLocationController.find_for_product")
            check_read(auth["role"], "bin_locations")
            bin_location = await self.CRUDBin.get_by_product_and_warehouse(
                product_id=product_id, warehouse_id=warehouse_id
            )
            if bin_location is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bin location not found")
            return self._format(bin_location)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in BinLocationController.find_for_product: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def update(self, bin_id: str, data: Dict[str, Any], auth: Dict[str, Any]) -> dict:
        """Update a bin location (admin/manager).

        Args:
            bin_id: Bin location id.
            data: Update data.
            auth: Authenticated user.

        Returns:
            dict: Updated bin location payload.
        """
        try:
            logging.info("Executing BinLocationController.update")
            require_roles(auth["role"], [UserRole.ADMIN.value, UserRole.MANAGER.value])
            payload = {k: v for k, v in data.items() if v is not None}
            if "product_id" in data and data["product_id"]:
                payload["product_id"] = ObjectId(data["product_id"])
                payload["is_occupied"] = True
            updated = await self.CRUDBin.update(id=bin_id, update_data=payload)
            if updated is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bin location not found")
            return self._format(updated)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in BinLocationController.update: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    @staticmethod
    def _format(b) -> dict:
        """Format a bin location for response.

        Args:
            b: Bin location document.

        Returns:
            dict: Response payload.
        """
        return {
            "id": str(b["_id"]),
            "warehouse_id": str(b["warehouse_id"]),
            "bin_code": b["bin_code"],
            "aisle": b["aisle"],
            "row": b["row"],
            "shelf": b["shelf"],
            "bin": b["bin"],
            "product_id": str(b["product_id"]) if b.get("product_id") else None,
            "max_capacity": b.get("max_capacity", 100),
            "current_units": b.get("current_units", 0),
            "is_occupied": b.get("is_occupied", False),
        }

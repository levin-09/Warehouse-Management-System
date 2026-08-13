"""Warehouse controller."""
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import HTTPException, status

from core import logger
from core.cruds.warehouse_crud import CRUDWarehouse
from core.models.enums import UserRole
from core.utils.rbac import require_roles

logging = logger(__name__)


class WarehouseController:
    """Orchestrates warehouse management."""

    def __init__(self) -> None:
        """Initialize the warehouse CRUD."""
        self.CRUDWarehouse = CRUDWarehouse()

    async def create(self, data: Dict[str, Any], auth: Dict[str, Any]) -> dict:
        """Create a warehouse (admin only).

        Args:
            data: Warehouse data.
            auth: Authenticated user.

        Returns:
            dict: Created warehouse payload.

        Raises:
            HTTPException 403: Not admin.
            HTTPException 400: Name already in use.
        """
        try:
            logging.info("Executing WarehouseController.create")
            require_roles(auth["role"], [UserRole.ADMIN.value])
            if await self.CRUDWarehouse.get_by_name(name=data["name"]):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Warehouse name already exists")
            warehouse = await self.CRUDWarehouse.create(obj_in=data)
            return self._format(warehouse)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in WarehouseController.create: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def list(self, auth: Dict[str, Any]) -> List[dict]:
        """List warehouses visible to the caller.

        Args:
            auth: Authenticated user.

        Returns:
            List[dict]: Warehouse payloads.
        """
        try:
            logging.info("Executing WarehouseController.list")
            warehouses = await self.CRUDWarehouse.list(query={})
            return [self._format(w) for w in warehouses]
        except Exception as error:
            logging.error(f"Error in WarehouseController.list: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def get(self, warehouse_id: str, auth: Dict[str, Any]) -> dict:
        """Fetch a single warehouse.

        Args:
            warehouse_id: Warehouse id.
            auth: Authenticated user.

        Returns:
            dict: Warehouse payload.

        Raises:
            HTTPException 404: Not found.
        """
        try:
            logging.info("Executing WarehouseController.get")
            warehouse = await self.CRUDWarehouse.get_by_id(id=warehouse_id)
            if warehouse is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")
            return self._format(warehouse)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in WarehouseController.get: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def update(self, warehouse_id: str, data: Dict[str, Any], auth: Dict[str, Any]) -> dict:
        """Update a warehouse (admin only).

        Args:
            warehouse_id: Warehouse id.
            data: Update data.
            auth: Authenticated user.

        Returns:
            dict: Updated warehouse payload.
        """
        try:
            logging.info("Executing WarehouseController.update")
            require_roles(auth["role"], [UserRole.ADMIN.value])
            warehouse = await self.CRUDWarehouse.get_by_id(id=warehouse_id)
            if warehouse is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")
            payload = {k: v for k, v in data.items() if v is not None}
            updated = await self.CRUDWarehouse.update(id=warehouse_id, update_data=payload)
            return self._format(updated)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in WarehouseController.update: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    @staticmethod
    def _format(w) -> dict:
        """Format a warehouse document for response.

        Args:
            w: Warehouse document.

        Returns:
            dict: Response payload.
        """
        return {
            "id": str(w["_id"]),
            "name": w["name"],
            "city": w["city"],
            "state": w["state"],
            "address": w["address"],
            "is_active": w.get("is_active", True),
            "carrier_schedules": w.get("carrier_schedules", []),
            "operating_hours": w.get("operating_hours"),
        }

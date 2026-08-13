"""Inventory controller — live stock queries and adjustments."""
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import HTTPException, status

from core import logger
from core.cruds.audit_log_crud import CRUDAuditLog
from core.cruds.inventory_crud import CRUDInventory
from core.cruds.product_crud import CRUDProduct
from core.models.enums import AuditMethod, UserRole
from core.utils.custom.database_helper import utc_timestamp
from core.utils.rbac import check_read, check_write, require_roles

logging = logger(__name__)


class InventoryController:
    """Orchestrates inventory queries and adjustments."""

    def __init__(self) -> None:
        """Initialize inventory, product, and audit CRUDs."""
        self.CRUDInventory = CRUDInventory()
        self.CRUDProduct = CRUDProduct()
        self.CRUDAudit = CRUDAuditLog()

    async def stock_by_upc(self, upc: str, warehouse_id: str, auth: Dict[str, Any]) -> dict:
        """Return live stock for a product at a warehouse.

        Args:
            upc: Product UPC barcode.
            warehouse_id: Warehouse id.
            auth: Authenticated user.

        Returns:
            dict: Stock level payload.

        Raises:
            HTTPException 404: Product not found.
        """
        try:
            logging.info("Executing InventoryController.stock_by_upc")
            check_read(auth["role"], "inventory")
            product = await self.CRUDProduct.get_by_upc(upc_barcode=upc)
            if product is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
            inv = await self.CRUDInventory.get_by_product_and_warehouse(
                product_id=product["_id"], warehouse_id=warehouse_id
            )
            if inv is None:
                return self._stock_payload(product, warehouse_id, None)
            return self._stock_payload(product, warehouse_id, inv)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in InventoryController.stock_by_upc: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def low_stock(self, auth: Dict[str, Any], warehouse_id: str = "") -> List[dict]:
        """List products at or below their low-stock threshold.

        Args:
            auth: Authenticated user.
            warehouse_id: Optional warehouse filter.

        Returns:
            List[dict]: Low-stock inventory payloads.
        """
        try:
            logging.info("Executing InventoryController.low_stock")
            check_read(auth["role"], "inventory")
            query: Dict[str, Any] = {}
            if warehouse_id:
                query["warehouse_id"] = ObjectId(warehouse_id)
            elif auth.get("warehouse_id"):
                query["warehouse_id"] = ObjectId(auth["warehouse_id"])
            all_inv = await self.CRUDInventory.list(query=query)
            for inv in all_inv:
                product = await self.CRUDProduct.get_by_id(id=inv["product_id"])
                if product is None:
                    continue
                threshold = product.get("low_stock_threshold", 20)
                if inv.get("quantity_available", 0) <= threshold:
                    results.append(self._stock_payload(product, inv["warehouse_id"], inv))
            return results
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in InventoryController.low_stock: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def adjust(self, inventory_id: str, data: Dict[str, Any], auth: Dict[str, Any]) -> dict:
        """Adjust inventory counts (admin/manager).

        Args:
            inventory_id: Inventory id.
            data: Adjustment data.
            auth: Authenticated user.

        Returns:
            dict: Updated inventory payload.

        Raises:
            HTTPException 403: Insufficient permissions.
            HTTPException 404: Inventory not found.
        """
        try:
            logging.info("Executing InventoryController.adjust")
            require_roles(auth["role"], [UserRole.ADMIN.value, UserRole.MANAGER.value])
            check_write(auth["role"], "inventory")
            inv = await self.CRUDInventory.get_by_id(id=inventory_id)
            if inv is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory not found")
            old = dict(inv)
            updated = await self.CRUDInventory.adjust(inventory_id=inventory_id, update_data=data)
            await self.CRUDAudit.create(
                obj_in={
                    "user_id": ObjectId(auth["id"]),
                    "user_name": auth.get("full_name", ""),
                    "action": "inventory_adjustment",
                    "collection_name": "inventory",
                    "record_id": inv["_id"],
                    "warehouse_id": inv["warehouse_id"],
                    "old_value": old,
                    "new_value": updated,
                    "method": AuditMethod.MANUAL_ENTRY.value,
                    "created_at": utc_timestamp(),
                }
            )
            return self._format(updated)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in InventoryController.adjust: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def list(self, auth: Dict[str, Any], warehouse_id: str = "") -> List[dict]:
        """List inventory records.

        Args:
            auth: Authenticated user.
            warehouse_id: Optional warehouse filter.

        Returns:
            List[dict]: Inventory payloads.
        """
        try:
            logging.info("Executing InventoryController.list")
            check_read(auth["role"], "inventory")
            query: Dict[str, Any] = {}
            if warehouse_id:
                query["warehouse_id"] = ObjectId(warehouse_id)
            elif auth.get("warehouse_id"):
                query["warehouse_id"] = ObjectId(auth["warehouse_id"])
            invs = await self.CRUDInventory.list(query=query)
            return [self._format(i) for i in invs]
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in InventoryController.list: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    @staticmethod
    def _stock_payload(product, warehouse_id, inv) -> dict:
        """Build a stock-level payload.

        Args:
            product: Product document.
            warehouse_id: Warehouse id.
            inv: Inventory document or None.

        Returns:
            dict: Stock payload.
        """
        inv = inv or {}
        return {
            "product_id": str(product["_id"]),
            "product_name": product["product_name"],
            "upc_barcode": product["upc_barcode"],
            "warehouse_id": str(warehouse_id),
            "quantity_good": inv.get("quantity_good", 0),
            "quantity_damaged": inv.get("quantity_damaged", 0),
            "quantity_reserved": inv.get("quantity_reserved", 0),
            "quantity_available": inv.get("quantity_available", 0),
            "bin_location": inv.get("bin_location", ""),
        }

    @staticmethod
    def _format(inv) -> dict:
        """Format an inventory document for response.

        Args:
            inv: Inventory document.

        Returns:
            dict: Response payload.
        """
        return {
            "id": str(inv["_id"]),
            "product_id": str(inv["product_id"]),
            "warehouse_id": str(inv["warehouse_id"]),
            "seller_id": str(inv["seller_id"]),
            "quantity_good": inv.get("quantity_good", 0),
            "quantity_damaged": inv.get("quantity_damaged", 0),
            "quantity_reserved": inv.get("quantity_reserved", 0),
            "quantity_available": inv.get("quantity_available", 0),
            "bin_location": inv.get("bin_location", ""),
            "last_updated": inv.get("last_updated", ""),
            "last_updated_by": str(inv["last_updated_by"]) if inv.get("last_updated_by") else None,
        }

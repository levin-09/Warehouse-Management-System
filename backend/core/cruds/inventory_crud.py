"""Inventory persistence operations, including atomic stock mutations.

Stock reservations and releases use atomic ``find_one_and_update`` calls with
guards (``$gte``) so concurrent operations cannot oversell available stock.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from bson import ObjectId

from core import logger
from core.cruds.base_crud import BaseCRUD
from core.utils.custom.database_helper import str_to_object_id

logging = logger(__name__)


class CRUDInventory(BaseCRUD):
    """Database access layer for inventory records."""

    COLLECTION_NAME = "inventory"

    async def get_by_product_and_warehouse(
        self, *, product_id: Any, warehouse_id: Any
    ) -> Optional[Dict[str, Any]]:
        """Fetch inventory for a product at a warehouse.

        Args:
            product_id: Product id.
            warehouse_id: Warehouse id.

        Returns:
            Optional[dict]: The inventory document, or None.
        """
        return await self.get_one(
            query={
                "product_id": str_to_object_id(product_id),
                "warehouse_id": str_to_object_id(warehouse_id),
            }
        )

    async def reserve_stock(self, *, product_id: Any, warehouse_id: Any, quantity: int) -> Optional[Dict[str, Any]]:
        """Atomically reserve stock for an order if available.

        Only succeeds when ``quantity_available >= quantity``. Returns the updated
        document, or None when there is insufficient stock.

        Args:
            product_id: Product id.
            warehouse_id: Warehouse id.
            quantity: Units to reserve.

        Returns:
            Optional[dict]: Updated inventory document, or None if unavailable.
        """
        try:
            logging.info("Executing CRUDInventory.reserve_stock")
            result = await self.coll.find_one_and_update(
                {
                    "product_id": str_to_object_id(product_id),
                    "warehouse_id": str_to_object_id(warehouse_id),
                    "quantity_available": {"$gte": quantity},
                },
                {
                    "$inc": {"quantity_reserved": quantity, "quantity_available": -quantity},
                    "$set": {"last_updated": datetime.now(timezone.utc).isoformat()},
                },
                return_document=True,
            )
            return result
        except Exception as error:
            logging.error(f"Error in CRUDInventory.reserve_stock: {error}")
            raise

    async def release_reservation(self, *, product_id: Any, warehouse_id: Any, quantity: int) -> Optional[Dict[str, Any]]:
        """Release a stock reservation back to available.

        Used when an order is cancelled. Cannot drive reserved below zero.

        Args:
            product_id: Product id.
            warehouse_id: Warehouse id.
            quantity: Units to release.

        Returns:
            Optional[dict]: Updated inventory document, or None.
        """
        try:
            logging.info("Executing CRUDInventory.release_reservation")
            result = await self.coll.find_one_and_update(
                {
                    "product_id": str_to_object_id(product_id),
                    "warehouse_id": str_to_object_id(warehouse_id),
                    "quantity_reserved": {"$gte": quantity},
                },
                {
                    "$inc": {"quantity_reserved": -quantity, "quantity_available": quantity},
                    "$set": {"last_updated": datetime.now(timezone.utc).isoformat()},
                },
                return_document=True,
            )
            return result
        except Exception as error:
            logging.error(f"Error in CRUDInventory.release_reservation: {error}")
            raise

    async def confirm_shipment(self, *, product_id: Any, warehouse_id: Any, quantity: int) -> Optional[Dict[str, Any]]:
        """Decrement good stock when an order ships.

        Reserved is reduced first; available is unchanged because the units were
        already reserved.

        Args:
            product_id: Product id.
            warehouse_id: Warehouse id.
            quantity: Units shipped.

        Returns:
            Optional[dict]: Updated inventory document, or None.
        """
        try:
            logging.info("Executing CRUDInventory.confirm_shipment")
            result = await self.coll.find_one_and_update(
                {
                    "product_id": str_to_object_id(product_id),
                    "warehouse_id": str_to_object_id(warehouse_id),
                    "quantity_reserved": {"$gte": quantity},
                },
                {
                    "$inc": {"quantity_good": -quantity, "quantity_reserved": -quantity},
                    "$set": {"last_updated": datetime.now(timezone.utc).isoformat()},
                },
                return_document=True,
            )
            return result
        except Exception as error:
            logging.error(f"Error in CRUDInventory.confirm_shipment: {error}")
            raise

    async def receive_stock(self, *, product_id: Any, warehouse_id: Any, seller_id: Any = None, good: int = 0, damaged: int = 0, by: Any = None) -> Optional[Dict[str, Any]]:
        """Increase good and damaged stock on shipment receipt.

        Good and available both increase by ``good``; damaged increases by ``damaged``.
        Upserts a new inventory row when the product has not been received before.

        Args:
            product_id: Product id.
            warehouse_id: Warehouse id.
            seller_id: Seller id (used on upsert).
            good: Good units received.
            damaged: Damaged units received.
            by: User id performing the update.

        Returns:
            Optional[dict]: Updated inventory document, or None.
        """
        try:
            logging.info("Executing CRUDInventory.receive_stock")
            now = datetime.now(timezone.utc).isoformat()
            result = await self.coll.find_one_and_update(
                {
                    "product_id": str_to_object_id(product_id),
                    "warehouse_id": str_to_object_id(warehouse_id),
                },
                {
                    "$inc": {"quantity_good": good, "quantity_available": good, "quantity_damaged": damaged},
                    "$setOnInsert": {"seller_id": str_to_object_id(seller_id) if seller_id else None},
                    "$set": {
                        "last_updated": now,
                        "last_updated_by": str_to_object_id(by) if by else None,
                    },
                },
                upsert=True,
                return_document=True,
            )
            return result
        except Exception as error:
            logging.error(f"Error in CRUDInventory.receive_stock: {error}")
            raise

    async def adjust(self, *, inventory_id: Any, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Apply a stock adjustment, recomputing available = good - reserved.

        Args:
            inventory_id: Inventory document id.
            update_data: Fields to set (quantity_good, quantity_damaged, bin_location).

        Returns:
            Optional[dict]: Updated inventory document, or None.
        """
        try:
            logging.info("Executing CRUDInventory.adjust")
            current = await self.get_by_id(id=inventory_id)
            if current is None:
                return None
            good = int(update_data.get("quantity_good", current.get("quantity_good", 0)))
            reserved = int(current.get("quantity_reserved", 0))
            if good < reserved:
                good = reserved
            payload = {
                "quantity_good": good,
                "quantity_available": good - reserved,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
            if "quantity_damaged" in update_data:
                payload["quantity_damaged"] = int(update_data["quantity_damaged"])
            if "bin_location" in update_data:
                payload["bin_location"] = update_data["bin_location"]
            return await self.update(id=inventory_id, update_data=payload)
        except Exception as error:
            logging.error(f"Error in CRUDInventory.adjust: {error}")
            raise

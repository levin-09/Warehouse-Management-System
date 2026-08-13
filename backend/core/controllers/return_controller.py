"""Return controller — structured customer return processing."""
from typing import Any, Dict, List

from bson import ObjectId
from fastapi import HTTPException, status

from core import logger
from core.cruds.audit_log_crud import CRUDAuditLog
from core.cruds.damage_crud import CRUDDamageRecord
from core.cruds.inventory_crud import CRUDInventory
from core.cruds.order_crud import CRUDOrder
from core.cruds.return_crud import CRUDReturn
from core.models.enums import (
    AuditMethod,
    ReturnAction,
    ReturnCondition,
    ReturnStatus,
    UserRole,
)
from core.services.notification_service import NotificationService
from core.utils.custom.database_helper import utc_timestamp
from core.utils.rbac import check_write, require_roles

logging = logger(__name__)


class ReturnController:
    """Orchestrates customer returns from creation to disposition."""

    def __init__(self) -> None:
        """Initialize return, order, inventory, damage, and audit CRUDs."""
        self.CRUDReturn = CRUDReturn()
        self.CRUDOrder = CRUDOrder()
        self.CRUDInventory = CRUDInventory()
        self.CRUDDamage = CRUDDamageRecord()
        self.CRUDAudit = CRUDAuditLog()
        self.notifier = NotificationService()

    async def process(self, data: Dict[str, Any], auth: Dict[str, Any]) -> dict:
        """Process a return and apply its inventory disposition.

        Args:
            data: Return processing data.
            auth: Authenticated user.

        Returns:
            dict: Created return payload.

        Raises:
            HTTPException 403: Insufficient permissions.
            HTTPException 404: Original order not found.
        """
        try:
            logging.info("Executing ReturnController.process")
            require_roles(auth["role"], [UserRole.ADMIN.value, UserRole.MANAGER.value])
            check_write(auth["role"], "returns")
            order = await self.CRUDOrder.get_by_id(id=data["original_order_id"])
            if order is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Original order not found")

            warehouse_id = order["warehouse_id"]
            seller_id = order["seller_id"]

            items = []
            for item in data["items"]:
                condition = ReturnCondition(item["condition"])
                action = self._resolve_action(condition, item)
                items.append(
                    {
                        "product_id": ObjectId(item["product_id"]),
                        "product_name": item.get("product_name", ""),
                        "quantity": item["quantity"],
                        "condition": condition.value,
                        "damage_grade": item.get("damage_grade"),
                        "action_taken": action.value,
                    }
                )

            return_ref = f"RET-{await self.CRUDReturn.count(query={}) + 1}"
            return_doc = {
                "return_ref": return_ref,
                "original_order_id": order["_id"],
                "original_order_ref": order["order_ref"],
                "seller_id": seller_id,
                "warehouse_id": warehouse_id,
                "items": items,
                "return_reason": data.get("return_reason", ""),
                "status": ReturnStatus.COMPLETED.value,
                "processed_by": ObjectId(auth["id"]),
                "seller_notified": True,
                "completed_at": utc_timestamp(),
                "created_at": utc_timestamp(),
            }
            record = await self.CRUDReturn.create(obj_in=return_doc)

            for item in items:
                if item["action_taken"] == ReturnAction.RESTOCKED_TO_GOOD.value:
                    await self.CRUDInventory.receive_stock(
                        product_id=item["product_id"],
                        warehouse_id=warehouse_id,
                        seller_id=seller_id,
                        good=item["quantity"],
                        damaged=0,
                        by=auth["id"],
                    )
                elif item["condition"] == ReturnCondition.DAMAGED.value:
                    await self.CRUDDamage.create(
                        obj_in={
                            "product_id": item["product_id"],
                            "product_name": item["product_name"],
                            "seller_id": seller_id,
                            "warehouse_id": warehouse_id,
                            "quantity_damaged": item["quantity"],
                            "damage_grade": item.get("damage_grade") or "C",
                            "assessed_by": ObjectId(auth["id"]),
                            "action_taken": "placed_in_damaged",
                            "seller_notified": True,
                            "seller_notified_at": utc_timestamp(),
                        }
                    )

                await self.CRUDAudit.create(
                    obj_in={
                        "user_id": ObjectId(auth["id"]),
                        "user_name": auth.get("full_name", ""),
                        "action": "return_processed",
                        "collection_name": "inventory",
                        "record_id": item["product_id"],
                        "warehouse_id": warehouse_id,
                        "old_value": {},
                        "new_value": item,
                        "method": AuditMethod.MANUAL_ENTRY.value,
                        "created_at": utc_timestamp(),
                    }
                )

            await self.notifier.send(
                recipient_type="seller",
                recipient_id=seller_id,
                recipient_email="",
                channel="email",
                notification_type="return_processed",
                subject=f"Return {return_ref} processed",
                message=f"Return {return_ref} for order {order['order_ref']} processed.",
            )
            return self._format(record)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in ReturnController.process: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def list(self, auth: Dict[str, Any], warehouse_id: str = "") -> List[dict]:
        """List returns.

        Args:
            auth: Authenticated user.
            warehouse_id: Optional warehouse filter.

        Returns:
            List[dict]: Return payloads.
        """
        try:
            logging.info("Executing ReturnController.list")
            query: Dict[str, Any] = {}
            if warehouse_id:
                query["warehouse_id"] = ObjectId(warehouse_id)
            elif auth.get("warehouse_id"):
                query["warehouse_id"] = ObjectId(auth["warehouse_id"])
            returns = await self.CRUDReturn.list(query=query)
            return [self._format(r) for r in returns]
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in ReturnController.list: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def get(self, return_id: str, auth: Dict[str, Any]) -> dict:
        """Fetch a return.

        Args:
            return_id: Return id.
            auth: Authenticated user.

        Returns:
            dict: Return payload.
        """
        try:
            logging.info("Executing ReturnController.get")
            record = await self.CRUDReturn.get_by_id(id=return_id)
            if record is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return not found")
            return self._format(record)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in ReturnController.get: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    @staticmethod
    def _resolve_action(condition: ReturnCondition, item: dict) -> ReturnAction:
        """Resolve the disposition action for a returned item.

        Args:
            condition: Return condition.
            item: Return item data.

        Returns:
            ReturnAction: The disposition action.
        """
        if item.get("action_taken"):
            return ReturnAction(item["action_taken"])
        mapping = {
            ReturnCondition.RESELLABLE: ReturnAction.RESTOCKED_TO_GOOD,
            ReturnCondition.DAMAGED: ReturnAction.PLACED_IN_DAMAGED,
            ReturnCondition.UNSELLABLE: ReturnAction.RETURNED_TO_SELLER,
        }
        return mapping[condition]

    @staticmethod
    def _format(r) -> dict:
        """Format a return document for response.

        Args:
            r: Return document.

        Returns:
            dict: Response payload.
        """
        return {
            "id": str(r["_id"]),
            "return_ref": r["return_ref"],
            "original_order_id": str(r["original_order_id"]),
            "original_order_ref": r.get("original_order_ref", ""),
            "seller_id": str(r["seller_id"]),
            "warehouse_id": str(r["warehouse_id"]),
            "items": [
                {
                    "product_id": str(it["product_id"]),
                    "product_name": it.get("product_name", ""),
                    "quantity": it.get("quantity", 0),
                    "condition": it.get("condition"),
                    "damage_grade": it.get("damage_grade"),
                    "action_taken": it.get("action_taken"),
                }
                for it in r.get("items", [])
            ],
            "return_reason": r.get("return_reason", ""),
            "status": r.get("status"),
            "processed_by": str(r["processed_by"]) if r.get("processed_by") else None,
            "seller_notified": r.get("seller_notified", False),
            "completed_at": r.get("completed_at"),
        }

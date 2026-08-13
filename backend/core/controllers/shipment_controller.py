"""Shipment controller — inbound receiving workflow.

Implements duplicate-entry prevention (unique ref + pre-check) and the confirm
receipt transaction that updates inventory, writes audit logs, and records damage.
"""
from typing import Any, Dict, List

from bson import ObjectId
from fastapi import HTTPException, status

from core import logger
from core.cruds.audit_log_crud import CRUDAuditLog
from core.cruds.damage_crud import CRUDDamageRecord
from core.cruds.inventory_crud import CRUDInventory
from core.cruds.product_crud import CRUDProduct
from core.cruds.shipment_crud import CRUDShipment
from core.database.database import get_client
from core.models.enums import AuditMethod, DamageGrade, ShipmentStatus, UserRole
from core.services.notification_service import NotificationService
from core.utils.custom.database_helper import utc_timestamp
from core.utils.rbac import check_read, check_write, require_roles

logging = logger(__name__)


class ShipmentController:
    """Orchestrates inbound shipment receiving."""

    def __init__(self) -> None:
        """Initialize shipment, inventory, product, damage, and audit CRUDs."""
        self.CRUDShipment = CRUDShipment()
        self.CRUDInventory = CRUDInventory()
        self.CRUDProduct = CRUDProduct()
        self.CRUDDamage = CRUDDamageRecord()
        self.CRUDAudit = CRUDAuditLog()
        self.notifier = NotificationService()

    async def create_draft(self, data: Dict[str, Any], auth: Dict[str, Any]) -> dict:
        """Create a draft shipment after duplicate verification.

        Args:
            data: Draft shipment data.
            auth: Authenticated user.

        Returns:
            dict: Draft shipment payload.

        Raises:
            HTTPException 400: Duplicate shipment reference.
            HTTPException 403: Insufficient permissions.
        """
        try:
            logging.info("Executing ShipmentController.create_draft")
            check_write(auth["role"], "shipments")
            # Problem 1: duplicate entry prevention
            existing = await self.CRUDShipment.get_by_ref(shipment_ref=data["shipment_ref"])
            if existing:
                received_info = ""
                if existing.get("received_at"):
                    received_info = f" already received on {existing.get('received_at')}"
                logging.warning(f"Duplicate shipment ref {data['shipment_ref']} attempted")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"This shipment was{received_info}. "
                        "If this is a new delivery contact your manager."
                    ),
                )
            payload = dict(data)
            payload["seller_id"] = ObjectId(data["seller_id"])
            payload["warehouse_id"] = ObjectId(data["warehouse_id"])
            payload["status"] = ShipmentStatus.DRAFT.value
            items = []
            for item in data.get("items", []):
                items.append(
                    {
                        "product_id": ObjectId(item["product_id"]),
                        "upc_barcode": item.get("upc_barcode", ""),
                        "product_name": item.get("product_name", ""),
                        "quantity_expected": item.get("quantity_expected", 0),
                        "quantity_received": item.get("quantity_received", 0),
                        "quantity_damaged": item.get("quantity_damaged", 0),
                        "damage_grade": item.get("damage_grade"),
                        "damage_notes": item.get("damage_notes", ""),
                    }
                )
            payload["items"] = items
            shipment = await self.CRUDShipment.create(obj_in=payload)
            return self._format(shipment)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in ShipmentController.create_draft: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def confirm_receipt(self, data: Dict[str, Any], auth: Dict[str, Any]) -> dict:
        """Confirm receipt of a shipment and post its inventory effects.

        Runs a multi-document transaction: updates the shipment to received, applies
        inventory good/damaged changes, creates damage records, writes audit logs, and
        queues a seller notification.

        Args:
            data: Confirmation payload.
            auth: Authenticated user.

        Returns:
            dict: Confirmed shipment payload.

        Raises:
            HTTPException 400: Duplicate/shipment not found or no matching items.
            HTTPException 403: Insufficient permissions.
        """
        try:
            logging.info("Executing ShipmentController.confirm_receipt")
            check_write(auth["role"], "shipments")
            shipment = await self.CRUDShipment.get_by_ref(shipment_ref=data["shipment_ref"])
            if shipment is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
            if shipment.get("status") == ShipmentStatus.RECEIVED.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Shipment already confirmed as received",
                )

            warehouse_id = shipment["warehouse_id"]
            seller_id = shipment["seller_id"]
            updates = {str(item["product_id"]): item for item in data.get("items", [])}

            client = get_client()
            async with await client.start_session() as session:
                async with session.start_transaction():
                    for line in shipment.get("items", []):
                        update = updates.get(str(line["product_id"]))
                        if update is None:
                            update = {
                                "quantity_received": line.get("quantity_received", 0),
                                "quantity_damaged": line.get("quantity_damaged", 0),
                                "damage_grade": line.get("damage_grade"),
                                "damage_notes": line.get("damage_notes", ""),
                            }
                        good = int(update.get("quantity_received", 0)) - int(update.get("quantity_damaged", 0))
                        damaged = int(update.get("quantity_damaged", 0))

                        # Post inventory effects
                        await self.CRUDInventory.receive_stock(
                            product_id=line["product_id"],
                            warehouse_id=warehouse_id,
                            seller_id=seller_id,
                            good=good,
                            damaged=damaged,
                            by=auth["id"],
                        )
                        # Audit each inventory change
                        await self.CRUDAudit.create(
                            obj_in={
                                "user_id": ObjectId(auth["id"]),
                                "user_name": auth.get("full_name", ""),
                                "action": "shipment_received",
                                "collection_name": "inventory",
                                "record_id": line["product_id"],
                                "warehouse_id": warehouse_id,
                                "old_value": {"quantity_good": line.get("quantity_expected", 0)},
                                "new_value": {"quantity_good": good},
                                "method": AuditMethod.BARCODE_SCAN.value,
                                "created_at": utc_timestamp(),
                            }
                        )
                        # Damage records
                        if damaged and update.get("damage_grade"):
                            grade = DamageGrade(update["damage_grade"])
                            await self.CRUDDamage.create(
                                obj_in={
                                    "shipment_id": shipment["_id"],
                                    "shipment_ref": shipment["shipment_ref"],
                                    "product_id": line["product_id"],
                                    "product_name": line["product_name"],
                                    "seller_id": seller_id,
                                    "warehouse_id": warehouse_id,
                                    "quantity_damaged": damaged,
                                    "damage_grade": grade.value,
                                    "damage_notes": update.get("damage_notes", ""),
                                    "carrier": shipment.get("carrier", ""),
                                    "carrier_tracking": shipment["shipment_ref"],
                                    "assessed_by": ObjectId(auth["id"]),
                                    "action_taken": "placed_in_damaged" if grade.value in ("B", "C", "D") else "moved_to_good",
                                    "seller_notified": True,
                                    "seller_notified_at": utc_timestamp(),
                                }
                            )
                    # Finalize shipment with the confirmed item quantities.
                    final_items = []
                    for line in shipment.get("items", []):
                        update = updates.get(str(line["product_id"]))
                        if update is None:
                            update = {
                                "quantity_received": line.get("quantity_received", 0),
                                "quantity_damaged": line.get("quantity_damaged", 0),
                                "damage_grade": line.get("damage_grade"),
                                "damage_notes": line.get("damage_notes", ""),
                            }
                        final_items.append(
                            {
                                "product_id": line["product_id"],
                                "upc_barcode": line.get("upc_barcode", ""),
                                "product_name": line.get("product_name", ""),
                                "quantity_expected": line.get("quantity_expected", 0),
                                "quantity_received": int(update.get("quantity_received", 0)),
                                "quantity_damaged": int(update.get("quantity_damaged", 0)),
                                "damage_grade": update.get("damage_grade"),
                                "damage_notes": update.get("damage_notes", ""),
                            }
                        )
                    now = utc_timestamp()
                    await self.CRUDShipment.update(
                        id=shipment["_id"],
                        update_data={
                            "status": ShipmentStatus.RECEIVED.value,
                            "received_by": ObjectId(auth["id"]),
                            "received_at": now,
                            "notes": data.get("notes", shipment.get("notes", "")),
                            "items": final_items,
                        },
                    )
                    # Audit shipment receipt
                    await self.CRUDAudit.create(
                        obj_in={
                            "user_id": ObjectId(auth["id"]),
                            "user_name": auth.get("full_name", ""),
                            "action": "shipment_received",
                            "collection_name": "shipments",
                            "record_id": shipment["_id"],
                            "warehouse_id": warehouse_id,
                            "old_value": {"status": ShipmentStatus.DRAFT.value},
                            "new_value": {"status": ShipmentStatus.RECEIVED.value},
                            "method": AuditMethod.BARCODE_SCAN.value,
                            "created_at": now,
                        }
                    )
                    # Seller notification
                    await self.notifier.send(
                        recipient_type="seller",
                        recipient_id=seller_id,
                        recipient_email="",
                        channel="email",
                        notification_type="shipment_received",
                        subject=f"Shipment {shipment['shipment_ref']} received",
                        message=f"Shipment {shipment['shipment_ref']} received at warehouse {warehouse_id}.",
                    )

            confirmed = await self.CRUDShipment.get_by_id(id=shipment["_id"])
            return self._format(confirmed)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in ShipmentController.confirm_receipt: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def list(self, auth: Dict[str, Any], warehouse_id: str = "") -> List[dict]:
        """List shipments.

        Args:
            auth: Authenticated user.
            warehouse_id: Optional warehouse filter.

        Returns:
            List[dict]: Shipment payloads.
        """
        try:
            logging.info("Executing ShipmentController.list")
            check_read(auth["role"], "shipments")
            query: Dict[str, Any] = {}
            if warehouse_id:
                query["warehouse_id"] = ObjectId(warehouse_id)
            elif auth.get("warehouse_id"):
                query["warehouse_id"] = ObjectId(auth["warehouse_id"])
            shipments = await self.CRUDShipment.list(query=query)
            return [self._format(s) for s in shipments]
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in ShipmentController.list: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def get(self, shipment_id: str, auth: Dict[str, Any]) -> dict:
        """Fetch a shipment.

        Args:
            shipment_id: Shipment id.
            auth: Authenticated user.

        Returns:
            dict: Shipment payload.
        """
        try:
            logging.info("Executing ShipmentController.get")
            check_read(auth["role"], "shipments")
            shipment = await self.CRUDShipment.get_by_id(id=shipment_id)
            if shipment is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
            return self._format(shipment)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in ShipmentController.get: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    @staticmethod
    def _format(s) -> dict:
        """Format a shipment document for response.

        Args:
            s: Shipment document.

        Returns:
            dict: Response payload.
        """
        return {
            "id": str(s["_id"]),
            "shipment_ref": s["shipment_ref"],
            "seller_id": str(s["seller_id"]),
            "warehouse_id": str(s["warehouse_id"]),
            "carrier": s.get("carrier", ""),
            "status": s.get("status"),
            "received_by": str(s["received_by"]) if s.get("received_by") else None,
            "received_at": s.get("received_at"),
            "notes": s.get("notes", ""),
            "items": [
                {
                    "product_id": str(it["product_id"]),
                    "upc_barcode": it.get("upc_barcode", ""),
                    "product_name": it.get("product_name", ""),
                    "quantity_expected": it.get("quantity_expected", 0),
                    "quantity_received": it.get("quantity_received", 0),
                    "quantity_damaged": it.get("quantity_damaged", 0),
                    "damage_grade": it.get("damage_grade"),
                    "damage_notes": it.get("damage_notes", ""),
                }
                for it in s.get("items", [])
            ],
        }

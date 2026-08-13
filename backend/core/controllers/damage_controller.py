"""Damage record controller."""
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import HTTPException, status

from core import logger
from core.cruds.audit_log_crud import CRUDAuditLog
from core.cruds.damage_crud import CRUDDamageRecord
from core.cruds.inventory_crud import CRUDInventory
from core.cruds.product_crud import CRUDProduct
from core.models.enums import AuditMethod, DamageGrade, UserRole
from core.utils.custom.database_helper import utc_timestamp
from core.utils.rbac import check_read, check_write, require_roles

logging = logger(__name__)


class DamageController:
    """Orchestrates damage assessment records."""

    def __init__(self) -> None:
        """Initialize damage, inventory, product, and audit CRUDs."""
        self.CRUDDamage = CRUDDamageRecord()
        self.CRUDInventory = CRUDInventory()
        self.CRUDProduct = CRUDProduct()
        self.CRUDAudit = CRUDAuditLog()

    async def create(self, data: Dict[str, Any], auth: Dict[str, Any]) -> dict:
        """Create a damage record and reflect damaged stock.

        Grade A damage is recovered to good stock automatically (per case study).

        Args:
            data: Damage record data.
            auth: Authenticated user.

        Returns:
            dict: Created damage record payload.

        Raises:
            HTTPException 403: Insufficient permissions.
        """
        try:
            logging.info("Executing DamageController.create")
            check_write(auth["role"], "damage_records")
            grade = DamageGrade(data["damage_grade"])
            product = await self.CRUDProduct.get_by_id(id=data["product_id"])
            if product is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
            payload = dict(data)
            payload["product_id"] = ObjectId(data["product_id"])
            payload["product_name"] = product["product_name"]
            payload["warehouse_id"] = ObjectId(data["warehouse_id"])
            payload["seller_id"] = product["seller_id"]
            payload["assessed_by"] = ObjectId(auth["id"])
            payload["seller_notified"] = True
            payload["seller_notified_at"] = utc_timestamp()
            payload["action_taken"] = data.get("action_taken", self._default_action(grade))

            record = await self.CRUDDamage.create(obj_in=payload)

            # Grade A recovery: move damaged units back to good stock.
            if grade == DamageGrade.A:
                inv = await self.CRUDInventory.get_by_product_and_warehouse(
                    product_id=product["_id"], warehouse_id=data["warehouse_id"]
                )
                if inv:
                    await self.CRUDInventory.adjust(
                        inventory_id=inv["_id"],
                        update_data={"quantity_damaged": max(0, inv.get("quantity_damaged", 0) - data["quantity_damaged"])},
                    )
            await self.CRUDAudit.create(
                obj_in={
                    "user_id": ObjectId(auth["id"]),
                    "user_name": auth.get("full_name", ""),
                    "action": "damage_record_created",
                    "collection_name": "damage_records",
                    "record_id": record["_id"],
                    "warehouse_id": record["warehouse_id"],
                    "old_value": {},
                    "new_value": payload,
                    "method": AuditMethod.MANUAL_ENTRY.value,
                    "created_at": utc_timestamp(),
                }
            )
            return self._format(record)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in DamageController.create: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def list(self, auth: Dict[str, Any], warehouse_id: str = "") -> List[dict]:
        """List damage records.

        Args:
            auth: Authenticated user.
            warehouse_id: Optional warehouse filter.

        Returns:
            List[dict]: Damage record payloads.
        """
        try:
            logging.info("Executing DamageController.list")
            check_read(auth["role"], "damage_records")
            query: Dict[str, Any] = {}
            if warehouse_id:
                query["warehouse_id"] = ObjectId(warehouse_id)
            elif auth.get("warehouse_id"):
                query["warehouse_id"] = ObjectId(auth["warehouse_id"])
            records = await self.CRUDDamage.list(query=query)
            return [self._format(r) for r in records]
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in DamageController.list: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def get(self, damage_id: str, auth: Dict[str, Any]) -> dict:
        """Fetch a damage record.

        Args:
            damage_id: Damage record id.
            auth: Authenticated user.

        Returns:
            dict: Damage record payload.
        """
        try:
            logging.info("Executing DamageController.get")
            check_read(auth["role"], "damage_records")
            record = await self.CRUDDamage.get_by_id(id=damage_id)
            if record is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Damage record not found")
            return self._format(record)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in DamageController.get: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    @staticmethod
    def _default_action(grade: DamageGrade) -> str:
        """Return the default disposition action for a damage grade.

        Args:
            grade: Damage grade.

        Returns:
            str: Action label.
        """
        mapping = {
            DamageGrade.A: "moved_to_good",
            DamageGrade.B: "placed_in_discount_zone",
            DamageGrade.C: "held_for_seller",
            DamageGrade.D: "carrier_claim",
        }
        return mapping[grade]

    @staticmethod
    def _format(r) -> dict:
        """Format a damage record for response.

        Args:
            r: Damage record document.

        Returns:
            dict: Response payload.
        """
        return {
            "id": str(r["_id"]),
            "shipment_id": str(r["shipment_id"]) if r.get("shipment_id") else None,
            "shipment_ref": r.get("shipment_ref", ""),
            "product_id": str(r["product_id"]),
            "product_name": r.get("product_name", ""),
            "seller_id": str(r["seller_id"]),
            "warehouse_id": str(r["warehouse_id"]),
            "quantity_damaged": r.get("quantity_damaged", 0),
            "damage_grade": r.get("damage_grade"),
            "damage_notes": r.get("damage_notes", ""),
            "carrier": r.get("carrier", ""),
            "carrier_tracking": r.get("carrier_tracking", ""),
            "assessed_by": str(r["assessed_by"]) if r.get("assessed_by") else None,
            "action_taken": r.get("action_taken", ""),
            "seller_notified": r.get("seller_notified", False),
        }

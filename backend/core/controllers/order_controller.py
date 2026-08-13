"""Order controller — outbound order workflow.

Implements atomic stock reservation (Problem 2) and the shipped transaction that
consumes reserved stock and records the shipment.
"""
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import HTTPException, status

from core import logger
from core.cruds.audit_log_crud import CRUDAuditLog
from core.cruds.inventory_crud import CRUDInventory
from core.cruds.order_crud import CRUDOrder
from core.cruds.product_crud import CRUDProduct
from core.database.database import get_client
from core.models.enums import AuditMethod, OrderStatus, UserRole
from core.services.notification_service import NotificationService
from core.utils.custom.database_helper import utc_timestamp
from core.utils.rbac import check_read, check_write, require_roles

logging = logger(__name__)


class OrderController:
    """Orchestrates outbound order processing."""

    def __init__(self) -> None:
        """Initialize order, inventory, product, and audit CRUDs."""
        self.CRUDOrder = CRUDOrder()
        self.CRUDInventory = CRUDInventory()
        self.CRUDProduct = CRUDProduct()
        self.CRUDAudit = CRUDAuditLog()
        self.notifier = NotificationService()

    async def create_order(self, data: Dict[str, Any], auth: Dict[str, Any]) -> dict:
        """Create an order and reserve stock for its items.

        Reserves stock atomically inside a transaction so concurrent order
        confirmations cannot oversell available inventory.

        Args:
            data: Order creation data.
            auth: Authenticated user.

        Returns:
            dict: Created order payload.

        Raises:
            HTTPException 409: Insufficient stock for an item.
            HTTPException 400: Duplicate order reference.
        """
        try:
            logging.info("Executing OrderController.create_order")
            if await self.CRUDOrder.get_by_ref(order_ref=data["order_ref"]):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order reference already exists")

            items = []
            for item in data["items"]:
                product = await self.CRUDProduct.get_by_id(id=item["product_id"])
                if product is None:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
                items.append(
                    {
                        "product_id": ObjectId(item["product_id"]),
                        "upc_barcode": product["upc_barcode"],
                        "product_name": product["product_name"],
                        "quantity": item["quantity"],
                    }
                )

            order_doc = {
                "order_ref": data["order_ref"],
                "seller_id": ObjectId(data["seller_id"]),
                "warehouse_id": ObjectId(data["warehouse_id"]),
                "customer": data["customer"],
                "status": OrderStatus.PENDING.value,
                "assigned_to": ObjectId(data["assigned_to"]) if data.get("assigned_to") else None,
                "items": items,
                "created_at": utc_timestamp(),
            }

            client = get_client()
            order_id = None
            async with await client.start_session() as session:
                async with session.start_transaction():
                    # Reserve stock for every line atomically.
                    for item in items:
                        updated = await self.CRUDInventory.reserve_stock(
                            product_id=item["product_id"],
                            warehouse_id=data["warehouse_id"],
                            quantity=item["quantity"],
                        )
                        if updated is None:
                            logging.warning(
                                f"Insufficient stock for product {item['product_id']} "
                                f"needing {item['quantity']}"
                            )
                            raise HTTPException(
                                status_code=status.HTTP_409_CONFLICT,
                                detail=f"Insufficient stock for {item['product_name']}",
                            )
                        await self.CRUDAudit.create(
                            obj_in={
                                "user_id": ObjectId(auth["id"]),
                                "user_name": auth.get("full_name", ""),
                                "action": "stock_reserve",
                                "collection_name": "inventory",
                                "record_id": item["product_id"],
                                "warehouse_id": ObjectId(data["warehouse_id"]),
                                "old_value": {"quantity_reserved": updated["quantity_reserved"] - item["quantity"]},
                                "new_value": {"quantity_reserved": updated["quantity_reserved"]},
                                "method": AuditMethod.MANUAL_ENTRY.value,
                                "created_at": utc_timestamp(),
                            }
                        )
                    result = await self.CRUDOrder.coll.insert_one(order_doc)
                    order_id = result.inserted_id

            order = await self.CRUDOrder.get_by_id(id=order_id)
            return self._format(order)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in OrderController.create_order: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def update_status(
        self, order_id: str, new_status: str, auth: Dict[str, Any], shipping: Optional[Dict[str, Any]] = None
    ) -> dict:
        """Advance an order's status through its workflow.

        Shipped transitions consume reserved stock and write audit + notifications
        in a single transaction.

        Args:
            order_id: Order id.
            new_status: Target order status.
            auth: Authenticated user.
            shipping: Optional shipping details.

        Returns:
            dict: Updated order payload.

        Raises:
            HTTPException 404: Order not found.
            HTTPException 403: Invalid transition or access denied.
            HTTPException 400: Shipped without sufficient reservation.
        """
        try:
            logging.info("Executing OrderController.update_status")
            order = await self.CRUDOrder.get_by_id(id=order_id)
            if order is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

            require_roles(auth["role"], [UserRole.ADMIN.value, UserRole.MANAGER.value, UserRole.STAFF.value])
            if auth["role"] == UserRole.STAFF.value:
                if not (auth.get("id") and order.get("assigned_to") and str(order["assigned_to"]) == str(auth["id"])):
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Order not assigned to you")

            new_status_enum = OrderStatus(new_status)
            self._validate_transition(order["status"], new_status_enum)

            if new_status_enum == OrderStatus.SHIPPED:
                return await self._ship(order, auth, shipping)
            if new_status_enum == OrderStatus.CANCELLED:
                return await self._cancel(order, auth)

            extra = {}
            if new_status_enum == OrderStatus.LABELED and shipping:
                extra["shipping"] = {
                    "carrier": shipping.get("carrier", ""),
                    "tracking_number": shipping.get("tracking_number", ""),
                    "weight_lbs": shipping.get("weight_lbs", 0.0),
                    "ship_cost": shipping.get("ship_cost", 0.0),
                }
            updated = await self.CRUDOrder.update_status(id=order_id, status=new_status_enum.value, extra=extra)
            await self.CRUDAudit.create(
                obj_in={
                    "user_id": ObjectId(auth["id"]),
                    "user_name": auth.get("full_name", ""),
                    "action": "order_status_update",
                    "collection_name": "orders",
                    "record_id": order["_id"],
                    "warehouse_id": order["warehouse_id"],
                    "old_value": {"status": order["status"]},
                    "new_value": {"status": new_status_enum.value},
                    "method": AuditMethod.BARCODE_SCAN.value if auth.get("role") == UserRole.STAFF.value else AuditMethod.MANUAL_ENTRY.value,
                    "created_at": utc_timestamp(),
                }
            )
            return self._format(updated)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in OrderController.update_status: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def _ship(self, order, auth, shipping) -> dict:
        """Execute the shipped transition in a transaction.

        Args:
            order: Order document.
            auth: Authenticated user.
            shipping: Shipping details.

        Returns:
            dict: Updated order payload.

        Raises:
            HTTPException 500: Transaction failure.
        """
        client = get_client()
        async with await client.start_session() as session:
            async with session.start_transaction():
                for item in order["items"]:
                    updated = await self.CRUDInventory.confirm_shipment(
                        product_id=item["product_id"],
                        warehouse_id=order["warehouse_id"],
                        quantity=item["quantity"],
                    )
                    if updated is None:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Reservation missing for {item['product_name']}",
                        )
                    await self.CRUDAudit.create(
                        obj_in={
                            "user_id": ObjectId(auth["id"]),
                            "user_name": auth.get("full_name", ""),
                            "action": "order_shipped",
                            "collection_name": "inventory",
                            "record_id": item["product_id"],
                            "warehouse_id": order["warehouse_id"],
                            "old_value": {"quantity_reserved": updated["quantity_reserved"] + item["quantity"]},
                            "new_value": {"quantity_reserved": updated["quantity_reserved"]},
                            "method": AuditMethod.BARCODE_SCAN.value,
                            "created_at": utc_timestamp(),
                        }
                    )
                now = utc_timestamp()
                ship_payload = {
                    "carrier": (shipping or {}).get("carrier", ""),
                    "tracking_number": (shipping or {}).get("tracking_number", ""),
                    "weight_lbs": (shipping or {}).get("weight_lbs", 0.0),
                    "ship_cost": (shipping or {}).get("ship_cost", 0.0),
                    "shipped_at": now,
                }
                await self.CRUDOrder.update_status(
                    id=order["_id"], status=OrderStatus.SHIPPED.value, extra={"shipping": ship_payload}
                )
                await self.CRUDAudit.create(
                    obj_in={
                        "user_id": ObjectId(auth["id"]),
                        "user_name": auth.get("full_name", ""),
                        "action": "order_shipped",
                        "collection_name": "orders",
                        "record_id": order["_id"],
                        "warehouse_id": order["warehouse_id"],
                        "old_value": {"status": order["status"]},
                        "new_value": {"status": OrderStatus.SHIPPED.value, "shipping": ship_payload},
                        "method": AuditMethod.BARCODE_SCAN.value,
                        "created_at": now,
                    }
                )
                await self.notifier.send(
                    recipient_type="seller",
                    recipient_id=order["seller_id"],
                    recipient_email="",
                    channel="email",
                    notification_type="order_shipped",
                    subject=f"Order {order['order_ref']} shipped",
                    message=f"Order {order['order_ref']} shipped via {ship_payload['carrier']} "
                    f"tracking {ship_payload['tracking_number']}.",
                )
        return self._format(await self.CRUDOrder.get_by_id(id=order["_id"]))

    async def _cancel(self, order, auth) -> dict:
        """Cancel an order and release its reservations.

        Args:
            order: Order document.
            auth: Authenticated user.

        Returns:
            dict: Updated order payload.
        """
        for item in order["items"]:
            await self.CRUDInventory.release_reservation(
                product_id=item["product_id"], warehouse_id=order["warehouse_id"], quantity=item["quantity"]
            )
        updated = await self.CRUDOrder.update_status(id=order["_id"], status=OrderStatus.CANCELLED.value)
        await self.CRUDAudit.create(
            obj_in={
                "user_id": ObjectId(auth["id"]),
                "user_name": auth.get("full_name", ""),
                "action": "order_cancelled",
                "collection_name": "orders",
                "record_id": order["_id"],
                "warehouse_id": order["warehouse_id"],
                "old_value": {"status": order["status"]},
                "new_value": {"status": OrderStatus.CANCELLED.value},
                "method": AuditMethod.MANUAL_ENTRY.value,
                "created_at": utc_timestamp(),
            }
        )
        return self._format(updated)

    def _validate_transition(self, current: str, target: OrderStatus) -> None:
        """Validate an order status transition.

        Args:
            current: Current status.
            target: Target status.

        Raises:
            HTTPException 400: Invalid transition.
        """
        allowed = {
            OrderStatus.PENDING.value: {OrderStatus.PICKING.value, OrderStatus.CANCELLED.value},
            OrderStatus.PICKING.value: {OrderStatus.PACKED.value, OrderStatus.CANCELLED.value},
            OrderStatus.PACKED.value: {OrderStatus.LABELED.value, OrderStatus.CANCELLED.value},
            OrderStatus.LABELED.value: {OrderStatus.SHIPPED.value},
        }
        if target.value not in allowed.get(current, set()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid order status transition from {current} to {target.value}",
            )

    async def list(self, auth: Dict[str, Any], warehouse_id: str = "", assigned_only: bool = False) -> List[dict]:
        """List orders.

        Args:
            auth: Authenticated user.
            warehouse_id: Optional warehouse filter.
            assigned_only: Only orders assigned to the caller (staff).

        Returns:
            List[dict]: Order payloads.
        """
        try:
            logging.info("Executing OrderController.list")
            check_read(auth["role"], "orders")
            query: Dict[str, Any] = {}
            if assigned_only or auth["role"] == UserRole.STAFF.value:
                query["assigned_to"] = ObjectId(auth["id"])
            if warehouse_id:
                query["warehouse_id"] = ObjectId(warehouse_id)
            elif auth.get("warehouse_id"):
                query["warehouse_id"] = ObjectId(auth["warehouse_id"])
            orders = await self.CRUDOrder.list(query=query)
            return [self._format(o) for o in orders]
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in OrderController.list: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def get(self, order_id: str, auth: Dict[str, Any]) -> dict:
        """Fetch an order.

        Args:
            order_id: Order id.
            auth: Authenticated user.

        Returns:
            dict: Order payload.
        """
        try:
            logging.info("Executing OrderController.get")
            check_read(auth["role"], "orders")
            order = await self.CRUDOrder.get_by_id(id=order_id)
            if order is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
            return self._format(order)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in OrderController.get: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    @staticmethod
    def _format(o) -> dict:
        """Format an order document for response.

        Args:
            o: Order document.

        Returns:
            dict: Response payload.
        """
        return {
            "id": str(o["_id"]),
            "order_ref": o["order_ref"],
            "seller_id": str(o["seller_id"]),
            "warehouse_id": str(o["warehouse_id"]),
            "customer": o.get("customer", {}),
            "status": o.get("status"),
            "assigned_to": str(o["assigned_to"]) if o.get("assigned_to") else None,
            "items": [
                {
                    "product_id": str(it["product_id"]),
                    "upc_barcode": it.get("upc_barcode", ""),
                    "product_name": it.get("product_name", ""),
                    "quantity": it.get("quantity", 0),
                }
                for it in o.get("items", [])
            ],
            "shipping": o.get("shipping"),
        }

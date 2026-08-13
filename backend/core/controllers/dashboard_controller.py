"""Dashboard controller — aggregated management overview (admin)."""
from datetime import datetime, timezone
from typing import Any, Dict

from bson import ObjectId
from fastapi import HTTPException, status

from core import logger
from core.database.database import collection
from core.models.enums import UserRole
from core.utils.rbac import require_roles

logging = logger(__name__)


class DashboardController:
    """Builds the real-time management dashboard data."""

    async def overview(self, auth: Dict[str, Any]) -> dict:
        """Return aggregated dashboard data.

        Args:
            auth: Authenticated user.

        Returns:
            dict: Dashboard response payload.

        Raises:
            HTTPException 403: Not admin.
        """
        try:
            logging.info("Executing DashboardController.overview")
            require_roles(auth["role"], [UserRole.ADMIN.value])
            warehouses = await collection("warehouses").find({"is_active": True}).to_list(None)

            warehouse_cards = []
            inventory_overview = []
            today_start = datetime.now(timezone.utc).isoformat()[:10]

            for wh in warehouses:
                wh_id = wh["_id"]
                staff_active = await collection("users").count_documents({"warehouse_id": wh_id, "is_active": True})
                pending_orders = await collection("orders").count_documents(
                    {"warehouse_id": wh_id, "status": {"$in": ["pending", "picking", "packed"]}}
                )
                shipments_today = await collection("shipments").count_documents(
                    {"warehouse_id": wh_id, "status": "received", "received_at": {"$regex": f"^{today_start}"}}
                )
                alerts = await collection("inventory").count_documents(
                    {"warehouse_id": wh_id, "quantity_available": {"$lte": 0}}
                )
                warehouse_cards.append(
                    {
                        "warehouse_id": str(wh_id),
                        "warehouse_name": wh["name"],
                        "staff_active": staff_active,
                        "pending_orders": pending_orders,
                        "shipments_today": shipments_today,
                        "alerts": alerts,
                    }
                )

                skus = await collection("inventory").count_documents({"warehouse_id": wh_id})
                total_units = await self._sum_available(wh_id)
                low_stock = await self._low_stock_count(wh_id)
                out_stock = await collection("inventory").count_documents(
                    {"warehouse_id": wh_id, "quantity_available": 0}
                )
                inventory_overview.append(
                    {
                        "warehouse_id": str(wh_id),
                        "skus": skus,
                        "units": total_units,
                        "low_stock": low_stock,
                        "out_stock": out_stock,
                    }
                )

            activity_feed = await collection("audit_logs").find().sort("created_at", -1).limit(20).to_list(None)

            return {
                "warehouses": warehouse_cards,
                "inventory": inventory_overview,
                "activity_feed": [
                    {"id": str(a["_id"]), "user_name": a.get("user_name", ""), "action": a.get("action"), "created_at": a.get("created_at")}
                    for a in activity_feed
                ],
                "quick_stats": [
                    {"label": "Orders Shipped (30d)", "value": str(await self._orders_shipped_30d())},
                    {"label": "Shipments Received (30d)", "value": str(await self._shipments_30d())},
                    {"label": "Returns Processed", "value": str(await collection("returns").count_documents({}))},
                    {"label": "Active Sellers", "value": str(await collection("sellers").count_documents({"is_active": True}))},
                ],
            }
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in DashboardController.overview: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def _sum_available(self, wh_id: ObjectId) -> int:
        """Sum available stock across a warehouse.

        Args:
            wh_id: Warehouse id.

        Returns:
            int: Total available units.
        """
        rows = await collection("inventory").aggregate(
            [{"$match": {"warehouse_id": wh_id}}, {"$group": {"_id": None, "total": {"$sum": "$quantity_available"}}}]
        ).to_list(None)
        return rows[0]["total"] if rows else 0

    async def _low_stock_count(self, wh_id: ObjectId) -> int:
        """Count low-stock products at a warehouse.

        Args:
            wh_id: Warehouse id.

        Returns:
            int: Number of low-stock products.
        """
        products = await collection("products").find().to_list(None)
        invs = await collection("inventory").find({"warehouse_id": wh_id}).to_list(None)
        threshold_by_product = {str(p["_id"]): p.get("low_stock_threshold", 20) for p in products}
        count = 0
        for inv in invs:
            threshold = threshold_by_product.get(str(inv.get("product_id")), 20)
            if inv.get("quantity_available", 0) <= threshold:
                count += 1
        return count

    async def _orders_shipped_30d(self) -> int:
        """Count orders shipped in the last 30 days.

        Returns:
            int: Count.
        """
        from datetime import timedelta

        since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        return await collection("orders").count_documents(
            {"status": "shipped", "shipping.shipped_at": {"$gte": since}}
        )

    async def _shipments_30d(self) -> int:
        """Count shipments received in the last 30 days.

        Returns:
            int: Count.
        """
        from datetime import timedelta

        since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        return await collection("shipments").count_documents({"status": "received", "received_at": {"$gte": since}})

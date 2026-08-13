"""Scheduled automation jobs — plain, non-AI background tasks.

Implements the case study's "AI Agent" automation as ordinary scheduled jobs:
hourly health checks, low-stock alerts, daily summary, and monthly billing.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from core import logger
from core.cruds.inventory_crud import CRUDInventory
from core.cruds.product_crud import CRUDProduct
from core.cruds.seller_crud import CRUDSeller
from core.database.database import collection
from core.services.billing_service import BillingService
from core.services.forecasting_service import ForecastingService
from core.services.notification_service import NotificationService
from core.models.enums import NotificationChannel, NotificationType, RecipientType

logging = logger(__name__)


class SchedulerJobs:
    """Collection of scheduled background job handlers."""

    def __init__(self) -> None:
        """Initialize job dependencies."""
        self.inventory_crud = CRUDInventory()
        self.product_crud = CRUDProduct()
        self.seller_crud = CRUDSeller()
        self.notifier = NotificationService()
        self.billing = BillingService()
        self.forecasting = ForecastingService()

    async def hourly_checks(self) -> None:
        """Run hourly automated checks (low stock + stale orders).

        Sends low-stock alerts and flags stale orders. Never raises out of the
        scheduler; failures are logged.

        Returns:
            None
        """
        try:
            logging.info("Running hourly checks")
            await self._low_stock_check()
            await self._stale_order_check()
        except Exception as error:
            logging.error(f"Error in hourly checks: {error}")

    async def daily_summary(self) -> None:
        """Send the daily operational summary to the admin.

        Returns:
            None
        """
        try:
            logging.info("Running daily summary")
            today = datetime.now(timezone.utc).isoformat()[:10]
            admin = await collection("users").find_one({"role": "admin"})
            if admin is None:
                logging.warning("No admin user found for daily summary")
                return

            orders_today = await collection("orders").count_documents({"created_at": {"$regex": f"^{today}"}})
            shipped_today = await collection("orders").count_documents(
                {"status": "shipped", "shipping.shipped_at": {"$regex": f"^{today}"}}
            )
            pending = await collection("orders").count_documents({"status": "pending"})
            out_of_stock = await collection("inventory").count_documents({"quantity_available": 0})

            message = (
                f"Orders today: {orders_today} | Shipped today: {shipped_today} | "
                f"Still pending: {pending} | Out of stock: {out_of_stock}"
            )
            await self.notifier.send(
                recipient_type=RecipientType.USER.value,
                recipient_id=admin["_id"],
                recipient_email=admin["email"],
                channel=NotificationChannel.EMAIL.value,
                notification_type=NotificationType.DAILY_SUMMARY.value,
                subject="Daily Summary",
                message=message,
            )
        except Exception as error:
            logging.error(f"Error in daily summary: {error}")

    async def monthly_billing(self) -> None:
        """Generate monthly invoices for the previous month.

        Returns:
            None
        """
        try:
            logging.info("Running monthly billing")
            now = datetime.now(timezone.utc)
            prev = now.replace(day=1) - timedelta(days=1)
            await self.billing.generate_monthly_invoices(prev.year, prev.month)
        except Exception as error:
            logging.error(f"Error in monthly billing: {error}")

    async def hourly_forecasts(self) -> None:
        """Refresh inventory forecasts for all sellers.

        Returns:
            None
        """
        try:
            logging.info("Running hourly forecasts")
            await self.forecasting.run_for_all()
        except Exception as error:
            logging.error(f"Error in hourly forecasts: {error}")

    async def _low_stock_check(self) -> None:
        """Detect low-stock products and alert sellers.

        Returns:
            None
        """
        inventory_rows = await self.inventory_crud.list(query={})
        for inv in inventory_rows:
            product = await self.product_crud.get_by_id(id=inv["product_id"])
            if product is None:
                continue
            threshold = product.get("low_stock_threshold", 20)
            if inv.get("quantity_available", 0) <= threshold:
                seller = await self.seller_crud.get_by_id(id=inv["seller_id"])
                email = seller.get("email", "") if seller else ""
                await self.notifier.send(
                    recipient_type=RecipientType.SELLER.value,
                    recipient_id=inv["seller_id"],
                    recipient_email=email,
                    channel=NotificationChannel.EMAIL.value,
                    notification_type=NotificationType.LOW_STOCK_ALERT.value,
                    subject=f"Low Stock Alert: {product['product_name']}",
                    message=f"{product['product_name']} has {inv['quantity_available']} units available.",
                )

    async def _stale_order_check(self) -> None:
        """Flag orders stuck in pending/picking for over 48 hours.

        Returns:
            None
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        cursor = collection("orders").find(
            {"status": {"$in": ["pending", "picking"]}, "created_at": {"$lt": cutoff}}
        )
        stale = [doc async for doc in cursor]
        for order in stale:
            manager = await collection("users").find_one(
                {"role": "manager", "warehouse_id": order["warehouse_id"], "is_active": True}
            )
            if manager:
                await self.notifier.send(
                    recipient_type=RecipientType.USER.value,
                    recipient_id=manager["_id"],
                    recipient_email=manager["email"],
                    channel=NotificationChannel.IN_APP.value,
                    notification_type=NotificationType.STALE_ORDER.value,
                    subject=f"Stale order {order['order_ref']}",
                    message=f"Order {order['order_ref']} has been {order['status']} for over 48 hours.",
                )

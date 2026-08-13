"""Forecasting service — computes inventory forecasts per product.

Reads order history for sales velocity, current inventory for stock, and average
lead time from shipments to predict stockout and recommend reorder quantities.
Plain business logic (non-AI) matching the case study's forecasting formulas.
"""
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List

from bson import ObjectId

from core import logger
from core.cruds.forecast_crud import CRUDForecast
from core.cruds.inventory_crud import CRUDInventory
from core.database.database import collection
from core.models.enums import ConfidenceLevel
from core.utils.custom.database_helper import utc_timestamp

logging = logger(__name__)

SAFE_REORDER_BUFFER_DAYS = 2
SALES_WINDOW_DAYS = 30
TARGET_DAYS_BUFFER = 14


class ForecastingService:
    """Facade for computing and storing inventory forecasts."""

    def __init__(self) -> None:
        """Initialize forecast and inventory CRUDs."""
        self.crud_forecast = CRUDForecast()
        self.crud_inventory = CRUDInventory()

    async def run_for_seller(self, seller_id: Any) -> List[Dict[str, Any]]:
        """Compute forecasts for every inventory row of a seller.

        Args:
            seller_id: Seller id.

        Returns:
            List[dict]: Persisted forecast documents.

        Raises:
            Exception: If computation fails.
        """
        try:
            logging.info("Executing ForecastingService.run_for_seller")
            inventory_rows = await collection("inventory").find({"seller_id": seller_id}).to_list(None)
            lead_time = await self._avg_lead_time(seller_id)
            forecasts = []
            for row in inventory_rows:
                forecast = await self._compute_for_row(row, lead_time)
                if forecast:
                    forecasts.append(forecast)
            return forecasts
        except Exception as error:
            logging.error(f"Error in ForecastingService.run_for_seller: {error}")
            raise

    async def run_for_all(self) -> List[Dict[str, Any]]:
        """Compute forecasts for all sellers.

        Returns:
            List[dict]: Persisted forecast documents.

        Raises:
            Exception: If computation fails.
        """
        try:
            logging.info("Executing ForecastingService.run_for_all")
            seller_ids = await collection("sellers").distinct("_id", {"is_active": True})
            all_forecasts = []
            for seller_id in seller_ids:
                all_forecasts.extend(await self.run_for_seller(seller_id))
            return all_forecasts
        except Exception as error:
            logging.error(f"Error in ForecastingService.run_for_all: {error}")
            raise

    async def _compute_for_row(self, row: Dict[str, Any], lead_time: float) -> Dict[str, Any]:
        """Compute and persist a forecast for one inventory row.

        Args:
            row: Inventory document.
            lead_time: Average seller lead time in days.

        Returns:
            dict: The persisted forecast document, or None.
        """
        product_id = row["product_id"]
        warehouse_id = row["warehouse_id"]
        seller_id = row["seller_id"]

        product = await collection("products").find_one({"_id": product_id})
        if product is None:
            return None

        threshold = product.get("low_stock_threshold", 20)
        current_stock = int(row.get("quantity_available", 0))
        daily_rate = await self._daily_sales_rate(product_id, seller_id)

        days_remaining = (current_stock / daily_rate) if daily_rate else float("inf")
        predicted_date = None
        if daily_rate and current_stock > 0:
            predicted_date = (datetime.now(timezone.utc) + timedelta(days=days_remaining)).date().isoformat()

        recommended = int(TARGET_DAYS_BUFFER * daily_rate) if daily_rate else 0
        alert_sent = days_remaining <= (lead_time + SAFE_REORDER_BUFFER_DAYS)

        forecast = await self.crud_forecast.create(
            obj_in={
                "product_id": product_id,
                "seller_id": seller_id,
                "warehouse_id": warehouse_id,
                "calculated_at": utc_timestamp(),
                "current_stock": current_stock,
                "daily_sales_rate": round(daily_rate, 2),
                "days_remaining": round(days_remaining, 1),
                "predicted_stockout_date": predicted_date,
                "recommended_reorder_qty": recommended,
                "seller_lead_time_days": lead_time,
                "alert_sent": alert_sent,
                "seasonal_adjustment": False,
                "confidence_level": ConfidenceLevel.HIGH.value if daily_rate else ConfidenceLevel.LOW.value,
            }
        )
        logging.info(f"Forecast computed for product {product_id}")
        return forecast

    async def _daily_sales_rate(self, product_id: Any, seller_id: Any) -> float:
        """Compute average daily units sold over the sales window.

        Args:
            product_id: Product id.
            seller_id: Seller id.

        Returns:
            float: Daily sales rate.
        """
        since = datetime.now(timezone.utc) - timedelta(days=SALES_WINDOW_DAYS)
        pipeline = [
            {
                "$match": {
                    "seller_id": seller_id,
                    "status": "shipped",
                    "shipping.shipped_at": {"$gte": since.isoformat()},
                    "items.product_id": product_id,
                }
            },
            {"$unwind": "$items"},
            {"$match": {"items.product_id": product_id}},
            {"$group": {"_id": None, "total": {"$sum": "$items.quantity"}}},
        ]
        rows = await collection("orders").aggregate(pipeline).to_list(None)
        total = rows[0]["total"] if rows else 0
        return total / SALES_WINDOW_DAYS

    async def _avg_lead_time(self, seller_id: Any) -> float:
        """Estimate average seller lead time from shipment history.

        Uses a simple constant proxy since true pre-notification timestamps are not
        modeled; extend with real arrival data when available.

        Args:
            seller_id: Seller id.

        Returns:
            float: Average lead time in days.
        """
        return 5.0

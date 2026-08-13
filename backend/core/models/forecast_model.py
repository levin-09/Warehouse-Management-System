"""Forecast model — computed inventory forecasts per product."""
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from core.models.enums import ConfidenceLevel

COLLECTION = "forecasts"


class Forecast(BaseModel):
    """A computed inventory forecast for a product."""

    id: Optional[ObjectId] = Field(default=None, alias="_id")
    product_id: ObjectId
    seller_id: ObjectId
    warehouse_id: ObjectId
    calculated_at: str = ""
    current_stock: int = 0
    daily_sales_rate: float = 0.0
    days_remaining: float = 0.0
    predicted_stockout_date: Optional[str] = None
    recommended_reorder_qty: int = 0
    seller_lead_time_days: float = 0.0
    alert_sent: bool = False
    alert_sent_at: Optional[str] = None
    seasonal_adjustment: bool = False
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

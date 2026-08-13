"""Forecast response schemas."""
from typing import Optional

from pydantic import BaseModel

from core.models.enums import ConfidenceLevel


class ForecastResponse(BaseModel):
    """Forecast representation."""

    id: str
    product_id: str
    seller_id: str
    warehouse_id: str
    calculated_at: str
    current_stock: int
    daily_sales_rate: float
    days_remaining: float
    predicted_stockout_date: Optional[str] = None
    recommended_reorder_qty: int
    seller_lead_time_days: float
    alert_sent: bool
    seasonal_adjustment: bool
    confidence_level: ConfidenceLevel

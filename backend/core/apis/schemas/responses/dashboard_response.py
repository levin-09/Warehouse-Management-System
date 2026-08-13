"""Dashboard response schemas."""
from typing import List

from pydantic import BaseModel


class WarehouseOverview(BaseModel):
    """Per-warehouse summary card."""

    warehouse_id: str
    warehouse_name: str
    staff_active: int
    pending_orders: int
    shipments_today: int
    alerts: int


class InventoryOverviewItem(BaseModel):
    """Inventory metric for a warehouse."""

    warehouse_id: str
    skus: int
    units: int
    low_stock: int
    out_stock: int


class QuickStat(BaseModel):
    """A named quick statistic."""

    label: str
    value: str


class DashboardResponse(BaseModel):
    """Aggregated dashboard data."""

    warehouses: List[WarehouseOverview]
    inventory: List[InventoryOverviewItem]
    activity_feed: List[dict]
    quick_stats: List[QuickStat]

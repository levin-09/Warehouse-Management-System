"""Seller response schemas."""
from pydantic import BaseModel


class BillingRatesResponse(BaseModel):
    """Per-unit billing rates."""

    storage_per_unit_per_day: float
    fulfillment_per_order: float
    receiving_per_unit: float


class SellerResponse(BaseModel):
    """Seller representation (no portal password hash)."""

    id: str
    company_name: str
    contact_name: str
    email: str
    phone: str
    billing_rates: BillingRatesResponse
    low_stock_threshold_default: int
    is_active: bool

"""Seller request schemas."""
from typing import Optional

from pydantic import BaseModel, Field


class BillingRatesCreate(BaseModel):
    """Per-unit billing rates."""

    storage_per_unit_per_day: float = 0.05
    fulfillment_per_order: float = 3.50
    receiving_per_unit: float = 0.25


class SellerCreate(BaseModel):
    """Payload to create a seller."""

    company_name: str
    contact_name: str
    email: str
    phone: str
    billing_rates: BillingRatesCreate = Field(default_factory=BillingRatesCreate)
    portal_password: Optional[str] = None
    low_stock_threshold_default: int = 20
    is_active: bool = True


class SellerUpdate(BaseModel):
    """Payload to update a seller."""

    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    billing_rates: Optional[BillingRatesCreate] = None
    low_stock_threshold_default: Optional[int] = None
    is_active: Optional[bool] = None

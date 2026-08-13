"""Seller model — Dan's seller clients and their rates."""
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field

COLLECTION = "sellers"


class BillingRates(BaseModel):
    """Per-unit billing rates charged to a seller."""

    storage_per_unit_per_day: float = 0.05
    fulfillment_per_order: float = 3.50
    receiving_per_unit: float = 0.25


class SellerPortalLogin(BaseModel):
    """Credentials for the seller self-service portal."""

    email: str
    password_hash: str
    last_login: Optional[str] = None


class Seller(BaseModel):
    """A seller client of Whitfield Fulfillment."""

    id: Optional[ObjectId] = Field(default=None, alias="_id")
    company_name: str
    contact_name: str
    email: str
    phone: str
    billing_rates: BillingRates = Field(default_factory=BillingRates)
    portal_login: Optional[SellerPortalLogin] = None
    low_stock_threshold_default: int = 20
    is_active: bool = True

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

"""Invoice model — auto-generated monthly invoices per seller."""
from typing import List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from core.models.enums import InvoiceStatus

COLLECTION = "invoices"


class InvoicePeriod(BaseModel):
    """Billing period the invoice covers."""

    month: int
    year: int


class InvoiceLineItem(BaseModel):
    """A charge line on an invoice."""

    description: str
    units: float = 0.0
    days: float = 0.0
    rate: float = 0.0
    amount: float = 0.0


class Invoice(BaseModel):
    """A monthly seller invoice."""

    id: Optional[ObjectId] = Field(default=None, alias="_id")
    invoice_ref: str
    seller_id: ObjectId
    seller_name: str
    period: InvoicePeriod
    line_items: List[InvoiceLineItem] = Field(default_factory=list)
    subtotal: float = 0.0
    tax: float = 0.0
    total: float = 0.0
    status: InvoiceStatus = InvoiceStatus.DRAFT
    sent_at: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

"""Invoice response schemas."""
from typing import List

from pydantic import BaseModel

from core.models.enums import InvoiceStatus


class InvoicePeriodResponse(BaseModel):
    """Billing period."""

    month: int
    year: int


class InvoiceLineItemResponse(BaseModel):
    """A charge line."""

    description: str
    units: float
    days: float
    rate: float
    amount: float


class InvoiceResponse(BaseModel):
    """Invoice representation."""

    id: str
    invoice_ref: str
    seller_id: str
    seller_name: str
    period: InvoicePeriodResponse
    line_items: List[InvoiceLineItemResponse]
    subtotal: float
    tax: float
    total: float
    status: InvoiceStatus
    sent_at: str = ""

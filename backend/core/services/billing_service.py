"""Billing service — computes monthly seller invoices.

Calculates storage, fulfillment, and receiving fees from MongoDB aggregates, then
creates an invoice document. Mirrors the case study's automated billing flow as a
plain (non-AI) service.
"""
from calendar import monthrange
from datetime import date
from typing import Any, Dict, List

from bson import ObjectId

from core import logger
from core.cruds.invoice_crud import CRUDInvoice
from core.cruds.seller_crud import CRUDSeller
from core.database.database import collection
from core.models.enums import InvoiceStatus
from core.utils.custom.database_helper import utc_timestamp

logging = logger(__name__)


class BillingService:
    """Facade for monthly invoice generation."""

    def __init__(self) -> None:
        """Initialize invoice and seller CRUDs."""
        self.crud_invoice = CRUDInvoice()
        self.crud_seller = CRUDSeller()

    async def generate_monthly_invoices(self, year: int, month: int) -> List[Dict[str, Any]]:
        """Generate invoices for all active sellers for a period.

        Args:
            year: Billing year.
            month: Billing month (1-12).

        Returns:
            List[dict]: Created invoice documents.

        Raises:
            Exception: If generation fails.
        """
        try:
            logging.info("Executing BillingService.generate_monthly_invoices")
            sellers = await self.crud_seller.list(query={"is_active": True})
            invoices = []
            for seller in sellers:
                invoice = await self._build_invoice(seller, year, month)
                if invoice:
                    invoices.append(invoice)
            return invoices
        except Exception as error:
            logging.error(f"Error in BillingService.generate_monthly_invoices: {error}")
            raise

    async def _build_invoice(self, seller: Dict[str, Any], year: int, month: int) -> Dict[str, Any]:
        """Build and persist a single seller's invoice.

        Args:
            seller: Seller document.
            year: Billing year.
            month: Billing month.

        Returns:
            dict: The created invoice, or None if one already exists.

        Raises:
            Exception: If persistence fails.
        """
        seller_id = seller["_id"]
        existing = await self.crud_invoice.get_for_period(seller_id=seller_id, month=month, year=year)
        if existing:
            logging.info(f"Invoice already exists for {seller.get('company_name')} {year}-{month}")
            return existing

        rates = seller.get("billing_rates", {})
        start, end = self._period_bounds(year, month)

        storage_amount = await self._storage_fee(seller_id, month, year, rates)
        fulfillment_amount = await self._fulfillment_fee(seller_id, start, end, rates)
        receiving_amount = await self._receiving_fee(seller_id, start, end, rates)

        line_items = []
        if storage_amount:
            line_items.append({"description": "Storage fees", "units": 0, "days": 0, "rate": 0, "amount": round(storage_amount, 2)})
        if fulfillment_amount:
            line_items.append({"description": "Fulfillment fees", "units": 0, "days": 0, "rate": 0, "amount": round(fulfillment_amount, 2)})
        if receiving_amount:
            line_items.append({"description": "Receiving fees", "units": 0, "days": 0, "rate": 0, "amount": round(receiving_amount, 2)})

        subtotal = round(storage_amount + fulfillment_amount + receiving_amount, 2)
        invoice_ref = f"INV-{year}-{month:02d}-{str(seller_id)}"

        invoice = await self.crud_invoice.create(
            obj_in={
                "invoice_ref": invoice_ref,
                "seller_id": seller_id,
                "seller_name": seller.get("company_name"),
                "period": {"month": month, "year": year},
                "line_items": line_items,
                "subtotal": subtotal,
                "tax": 0,
                "total": subtotal,
                "status": InvoiceStatus.DRAFT.value,
                "created_at": utc_timestamp(),
            }
        )
        logging.info(f"Generated invoice {invoice_ref}")
        return invoice

    async def _storage_fee(self, seller_id: Any, month: int, year: int, rates: Dict[str, Any]) -> float:
        """Compute storage fees using average stock per product.

        Args:
            seller_id: Seller id.
            month: Billing month.
            year: Billing year.
            rates: Seller billing rates.

        Returns:
            float: Total storage fee.
        """
        days = monthrange(year, month)[1]
        rate = float(rates.get("storage_per_unit_per_day", 0))
        pipeline = [
            {"$match": {"seller_id": seller_id}},
            {"$group": {"_id": "$product_id", "avg_stock": {"$avg": "$quantity_good"}}},
        ]
        rows = await collection("inventory").aggregate(pipeline).to_list(None)
        total = sum(float(r["avg_stock"]) * days * rate for r in rows)
        return total

    async def _fulfillment_fee(self, seller_id: Any, start: str, end: str, rates: Dict[str, Any]) -> float:
        """Compute fulfillment fees from shipped order count.

        Args:
            seller_id: Seller id.
            start: Period start ISO string.
            end: Period end ISO string.
            rates: Seller billing rates.

        Returns:
            float: Total fulfillment fee.
        """
        rate = float(rates.get("fulfillment_per_order", 0))
        count = await collection("orders").count_documents(
            {
                "seller_id": seller_id,
                "status": "shipped",
                "shipping.shipped_at": {"$gte": start, "$lt": end},
            }
        )
        return count * rate

    async def _receiving_fee(self, seller_id: Any, start: str, end: str, rates: Dict[str, Any]) -> float:
        """Compute receiving fees from units received in shipments.

        Args:
            seller_id: Seller id.
            start: Period start ISO string.
            end: Period end ISO string.
            rates: Seller billing rates.

        Returns:
            float: Total receiving fee.
        """
        rate = float(rates.get("receiving_per_unit", 0))
        pipeline = [
            {
                "$match": {
                    "seller_id": seller_id,
                    "status": "received",
                    "received_at": {"$gte": start, "$lt": end},
                }
            },
            {"$unwind": "$items"},
            {"$group": {"_id": None, "total": {"$sum": "$items.quantity_received"}}},
        ]
        rows = await collection("shipments").aggregate(pipeline).to_list(None)
        total = rows[0]["total"] if rows else 0
        return total * rate

    @staticmethod
    def _period_bounds(year: int, month: int):
        """Return the start/end ISO timestamps for a billing period.

        Args:
            year: Billing year.
            month: Billing month.

        Returns:
            tuple: (start_iso, end_iso) for the month.
        """
        start = date(year, month, 1)
        end_day = monthrange(year, month)[1]
        end = date(year, month, end_day)
        return start.isoformat() + "T00:00:00Z", end.isoformat() + "T23:59:59Z"

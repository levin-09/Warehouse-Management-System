"""Invoice persistence operations."""
from typing import Any, Optional

from core.cruds.base_crud import BaseCRUD


class CRUDInvoice(BaseCRUD):
    """Database access layer for invoice records."""

    COLLECTION_NAME = "invoices"

    async def get_by_ref(self, *, invoice_ref: str) -> Optional[dict]:
        """Fetch an invoice by its reference number.

        Args:
            invoice_ref: Invoice reference.

        Returns:
            Optional[dict]: The invoice document, or None.
        """
        return await self.get_one(query={"invoice_ref": invoice_ref})

    async def get_for_period(self, *, seller_id: Any, month: int, year: int) -> Optional[dict]:
        """Fetch an existing invoice for a seller and period.

        Args:
            seller_id: Seller id.
            month: Billing month.
            year: Billing year.

        Returns:
            Optional[dict]: The invoice document, or None.
        """
        return await self.get_one(
            query={"seller_id": seller_id, "period.month": month, "period.year": year}
        )

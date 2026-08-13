"""Invoice controller."""
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import HTTPException, status

from core import logger
from core.cruds.invoice_crud import CRUDInvoice
from core.models.enums import UserRole
from core.services.billing_service import BillingService
from core.utils.rbac import require_roles

logging = logger(__name__)


class InvoiceController:
    """Orchestrates invoice listing and generation (admin only)."""

    def __init__(self) -> None:
        """Initialize invoice CRUD and billing service."""
        self.CRUDInvoice = CRUDInvoice()
        self.billing = BillingService()

    async def list(self, auth: Dict[str, Any], seller_id: str = "") -> List[dict]:
        """List invoices.

        Args:
            auth: Authenticated user.
            seller_id: Optional seller filter.

        Returns:
            List[dict]: Invoice payloads.

        Raises:
            HTTPException 403: Not admin.
        """
        try:
            logging.info("Executing InvoiceController.list")
            require_roles(auth["role"], [UserRole.ADMIN.value])
            query: Dict[str, Any] = {}
            if seller_id:
                query["seller_id"] = ObjectId(seller_id)
            invoices = await self.CRUDInvoice.list(query=query)
            return [self._format(i) for i in invoices]
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in InvoiceController.list: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def get(self, invoice_id: str, auth: Dict[str, Any]) -> dict:
        """Fetch an invoice.

        Args:
            invoice_id: Invoice id.
            auth: Authenticated user.

        Returns:
            dict: Invoice payload.
        """
        try:
            logging.info("Executing InvoiceController.get")
            require_roles(auth["role"], [UserRole.ADMIN.value])
            invoice = await self.CRUDInvoice.get_by_id(id=invoice_id)
            if invoice is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
            return self._format(invoice)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in InvoiceController.get: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def generate(self, year: int, month: int, auth: Dict[str, Any]) -> List[dict]:
        """Generate invoices for a period (admin only).

        Args:
            year: Billing year.
            month: Billing month.
            auth: Authenticated user.

        Returns:
            List[dict]: Generated invoice payloads.
        """
        try:
            logging.info("Executing InvoiceController.generate")
            require_roles(auth["role"], [UserRole.ADMIN.value])
            invoices = await self.billing.generate_monthly_invoices(year, month)
            return [self._format(i) for i in invoices]
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in InvoiceController.generate: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    @staticmethod
    def _format(i) -> dict:
        """Format an invoice document for response.

        Args:
            i: Invoice document.

        Returns:
            dict: Response payload.
        """
        return {
            "id": str(i["_id"]),
            "invoice_ref": i["invoice_ref"],
            "seller_id": str(i["seller_id"]),
            "seller_name": i.get("seller_name", ""),
            "period": i.get("period", {}),
            "line_items": i.get("line_items", []),
            "subtotal": i.get("subtotal", 0.0),
            "tax": i.get("tax", 0.0),
            "total": i.get("total", 0.0),
            "status": i.get("status"),
            "sent_at": i.get("sent_at", ""),
        }

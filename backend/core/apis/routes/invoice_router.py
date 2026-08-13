"""Invoice routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from commons.dependencies import get_current_user
from core import logger
from core.apis.schemas.responses.invoice_response import InvoiceResponse
from core.controllers.invoice_controller import InvoiceController

invoice_router = APIRouter(prefix="/v1/invoices", tags=["Invoices"])
logging = logger(__name__)


@invoice_router.get("", response_model=list[InvoiceResponse])
async def list_invoices(seller_id: Optional[str] = Query(default=None), auth: dict = Depends(get_current_user)):
    """
    List invoices (admin only).

    Args:
        seller_id (Optional[str]): Seller filter.
        auth (dict): Authenticated user claims.

    Returns:
        list[InvoiceResponse]: Invoices.
    """
    try:
        logging.info("Calling GET /v1/invoices endpoint")
        response = await InvoiceController().list(auth, seller_id or "")
        return [InvoiceResponse(**i) for i in response]
    except HTTPException as error:
        logging.error(f"Error in GET /v1/invoices endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/invoices endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@invoice_router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: str, auth: dict = Depends(get_current_user)):
    """
    Fetch an invoice by id (admin only).

    Args:
        invoice_id (str): Invoice id.
        auth (dict): Authenticated user claims.

    Returns:
        InvoiceResponse: Invoice.
    """
    try:
        logging.info(f"Calling GET /v1/invoices/{invoice_id} endpoint")
        response = await InvoiceController().get(invoice_id, auth)
        return InvoiceResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in GET /v1/invoices/{invoice_id} endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/invoices/{invoice_id} endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@invoice_router.post("/generate", response_model=list[InvoiceResponse])
async def generate_invoices(
    year: int = Query(...), month: int = Query(..., ge=1, le=12), auth: dict = Depends(get_current_user)
):
    """
    Generate invoices for a period (admin only).

    Args:
        year (int): Billing year.
        month (int): Billing month.
        auth (dict): Authenticated user claims.

    Returns:
        list[InvoiceResponse]: Generated invoices.
    """
    try:
        logging.info("Calling POST /v1/invoices/generate endpoint")
        response = await InvoiceController().generate(year, month, auth)
        return [InvoiceResponse(**i) for i in response]
    except HTTPException as error:
        logging.error(f"Error in POST /v1/invoices/generate endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in POST /v1/invoices/generate endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

"""Seller portal routes — seller-scoped read-only access to their own data."""
from fastapi import APIRouter, Depends, HTTPException, status

from commons.seller_deps import get_current_seller
from core import logger
from core.controllers.seller_portal_controller import SellerPortalController

seller_portal_router = APIRouter(prefix="/v1/seller", tags=["Seller Portal"])
logging = logger(__name__)

_controller = SellerPortalController()


async def _handle(coro, path: str):
    """Run a seller controller coroutine and convert errors.

    Args:
        coro: The coroutine to run.
        path: The request path for logging.

    Returns:
        The controller result.
    """
    try:
        return await coro
    except HTTPException:
        raise
    except Exception as error:
        logging.error(f"Error in seller portal {path}: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@seller_portal_router.get("/me")
async def me(seller: dict = Depends(get_current_seller)):
    """Return the seller's own profile.

    Args:
        seller: Seller identity from the token.

    Returns:
        dict: Seller profile.
    """
    return await _handle(_controller.me(seller["seller_id"]), "me")


@seller_portal_router.get("/products")
async def products(seller: dict = Depends(get_current_seller)):
    """List the seller's products.

    Args:
        seller: Seller identity from the token.

    Returns:
        list: The seller's products.
    """
    return await _handle(_controller.products(seller["seller_id"]), "products")


@seller_portal_router.get("/inventory")
async def inventory(seller: dict = Depends(get_current_seller)):
    """List the seller's inventory.

    Args:
        seller: Seller identity from the token.

    Returns:
        list: The seller's inventory.
    """
    return await _handle(_controller.inventory(seller["seller_id"]), "inventory")


@seller_portal_router.get("/orders")
async def orders(seller: dict = Depends(get_current_seller)):
    """List the seller's orders.

    Args:
        seller: Seller identity from the token.

    Returns:
        list: The seller's orders.
    """
    return await _handle(_controller.orders(seller["seller_id"]), "orders")


@seller_portal_router.get("/shipments")
async def shipments(seller: dict = Depends(get_current_seller)):
    """List the seller's shipments.

    Args:
        seller: Seller identity from the token.

    Returns:
        list: The seller's shipments.
    """
    return await _handle(_controller.shipments(seller["seller_id"]), "shipments")


@seller_portal_router.get("/invoices")
async def invoices(seller: dict = Depends(get_current_seller)):
    """List the seller's invoices.

    Args:
        seller: Seller identity from the token.

    Returns:
        list: The seller's invoices.
    """
    return await _handle(_controller.invoices(seller["seller_id"]), "invoices")


@seller_portal_router.get("/returns")
async def returns(seller: dict = Depends(get_current_seller)):
    """List the seller's returns.

    Args:
        seller: Seller identity from the token.

    Returns:
        list: The seller's returns.
    """
    return await _handle(_controller.returns(seller["seller_id"]), "returns")


@seller_portal_router.get("/notifications")
async def notifications(seller: dict = Depends(get_current_seller)):
    """List the seller's notifications.

    Args:
        seller: Seller identity from the token.

    Returns:
        list: The seller's notifications.
    """
    return await _handle(_controller.notifications(seller["seller_id"]), "notifications")

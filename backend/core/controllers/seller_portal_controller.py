"""Seller portal controller.

All queries are scoped to a single seller (from the seller token). A seller can
only ever see their own products, inventory, orders, shipments, invoices, returns,
and notifications.
"""
from typing import Any, Dict, List

from bson import ObjectId
from fastapi import HTTPException, status

from core import logger
from core.cruds.seller_crud import CRUDSeller
from core.database.database import collection
from core.utils.custom.database_helper import to_dict

logging = logger(__name__)


class SellerPortalController:
    """Exposes read-only, seller-scoped data for the seller portal."""

    def __init__(self) -> None:
        """Initialize the seller CRUD."""
        self.CRUDSeller = CRUDSeller()

    async def me(self, seller_id: Any) -> Dict[str, Any]:
        """Return the seller's own profile.

        Args:
            seller_id: Seller id from the token.

        Returns:
            dict: Seller profile (no portal password hash).
        """
        seller = await self.CRUDSeller.get_by_id(id=seller_id)
        if seller is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")
        return {
            "id": str(seller["_id"]),
            "company_name": seller.get("company_name"),
            "contact_name": seller.get("contact_name"),
            "email": seller.get("email"),
            "billing_rates": seller.get("billing_rates", {}),
            "low_stock_threshold_default": seller.get("low_stock_threshold_default", 20),
        }

    async def products(self, seller_id: Any) -> List[dict]:
        """List the seller's products.

        Args:
            seller_id: Seller id.

        Returns:
            list: The seller's products.
        """
        products = await collection("products").find({"seller_id": ObjectId(seller_id)}).to_list(None)
        return [to_dict(p) for p in products]

    async def inventory(self, seller_id: Any) -> List[dict]:
        """List the seller's inventory across all warehouses.

        Args:
            seller_id: Seller id.

        Returns:
            list: The seller's inventory rows.
        """
        rows = await collection("inventory").find({"seller_id": ObjectId(seller_id)}).to_list(None)
        warehouses = {w["_id"]: w["name"] for w in await collection("warehouses").find({}).to_list(None)}
        products = {p["_id"]: p["product_name"] for p in await collection("products").find({"seller_id": ObjectId(seller_id)}).to_list(None)}
        result = []
        for r in rows:
            result.append({
                "id": str(r["_id"]),
                "product_name": products.get(r.get("product_id"), str(r.get("product_id"))),
                "warehouse": warehouses.get(r.get("warehouse_id"), "?"),
                "quantity_good": r.get("quantity_good", 0),
                "quantity_damaged": r.get("quantity_damaged", 0),
                "quantity_reserved": r.get("quantity_reserved", 0),
                "quantity_available": r.get("quantity_available", 0),
                "last_updated": r.get("last_updated"),
            })
        return result

    async def orders(self, seller_id: Any) -> List[dict]:
        """List the seller's orders.

        Args:
            seller_id: Seller id.

        Returns:
            list: The seller's orders.
        """
        orders = await collection("orders").find({"seller_id": ObjectId(seller_id)}).sort("created_at", -1).to_list(None)
        warehouses = {w["_id"]: w["name"] for w in await collection("warehouses").find({}).to_list(None)}
        return [
            {
                "id": str(o["_id"]),
                "order_ref": o.get("order_ref"),
                "status": o.get("status"),
                "warehouse": warehouses.get(o.get("warehouse_id"), "?"),
                "customer": (o.get("customer") or {}).get("name"),
                "items": [
                    {"product": i.get("product_name"), "quantity": i.get("quantity")}
                    for i in o.get("items", [])
                ],
                "shipping": o.get("shipping"),
            }
            for o in orders
        ]

    async def shipments(self, seller_id: Any) -> List[dict]:
        """List the seller's inbound shipments.

        Args:
            seller_id: Seller id.

        Returns:
            list: The seller's shipments.
        """
        shipments = await collection("shipments").find({"seller_id": ObjectId(seller_id)}).sort("received_at", -1).to_list(None)
        warehouses = {w["_id"]: w["name"] for w in await collection("warehouses").find({}).to_list(None)}
        return [
            {
                "id": str(s["_id"]),
                "shipment_ref": s.get("shipment_ref"),
                "status": s.get("status"),
                "warehouse": warehouses.get(s.get("warehouse_id"), "?"),
                "carrier": s.get("carrier"),
                "received_at": s.get("received_at"),
                "items": [
                    {"product": i.get("product_name"), "received": i.get("quantity_received"), "expected": i.get("quantity_expected")}
                    for i in s.get("items", [])
                ],
            }
            for s in shipments
        ]

    async def invoices(self, seller_id: Any) -> List[dict]:
        """List the seller's invoices.

        Args:
            seller_id: Seller id.

        Returns:
            list: The seller's invoices.
        """
        invoices = await collection("invoices").find({"seller_id": ObjectId(seller_id)}).sort("created_at", -1).to_list(None)
        return [
            {
                "id": str(i["_id"]),
                "invoice_ref": i.get("invoice_ref"),
                "period": i.get("period"),
                "line_items": i.get("line_items", []),
                "total": i.get("total", 0),
                "status": i.get("status"),
            }
            for i in invoices
        ]

    async def returns(self, seller_id: Any) -> List[dict]:
        """List the seller's returns.

        Args:
            seller_id: Seller id.

        Returns:
            list: The seller's returns.
        """
        returns = await collection("returns").find({"seller_id": ObjectId(seller_id)}).sort("created_at", -1).to_list(None)
        return [
            {
                "id": str(r["_id"]),
                "return_ref": r.get("return_ref"),
                "original_order_ref": r.get("original_order_ref"),
                "status": r.get("status"),
                "items": r.get("items", []),
                "completed_at": r.get("completed_at"),
            }
            for r in returns
        ]

    async def notifications(self, seller_id: Any) -> List[dict]:
        """List the seller's notifications.

        Args:
            seller_id: Seller id.

        Returns:
            list: The seller's notifications.
        """
        notifs = await collection("notifications").find(
            {"recipient_type": "seller", "recipient_id": ObjectId(seller_id)}
        ).sort("created_at", -1).to_list(None)
        return [
            {
                "id": str(n["_id"]),
                "subject": n.get("subject"),
                "message": n.get("message"),
                "notification_type": n.get("notification_type"),
                "is_read": n.get("is_read"),
                "created_at": n.get("created_at"),
            }
            for n in notifs
        ]

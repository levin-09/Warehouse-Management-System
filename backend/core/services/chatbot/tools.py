"""WMS tools for the GenAI chatbot.

Replaces the reference ``genai_chatbot``'s Tavily web tools with tools that query
the Whitfield WMS MongoDB database directly. Each tool has a JSON schema (sent to
the model so it knows how to ask) and a Python function (what actually runs).

Only read-only queries live here. Write/action tools (recording receipts, updating
order status) belong to the voice bot's action layer, not to a general Q&A chatbot,
to keep the chatbot safe.
"""
from typing import Any, Dict

from bson import ObjectId

from core import logger
from core.database.database import collection
from core.utils.custom.database_helper import str_to_object_id, to_dict

logging = logger(__name__)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
async def _warehouse_id(name: str = "") -> Any:
    """Resolve a warehouse name to its ObjectId (or return None).

    Args:
        name: Warehouse name (e.g. "Reno", "Columbus"). Empty means no filter.

    Returns:
        Any: The warehouse ObjectId, or None if not found / not given.
    """
    if not name:
        return None
    wh = await collection("warehouses").find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
    return wh["_id"] if wh else None


def _err(msg: str) -> Dict[str, str]:
    """Build an error payload for the model to read.

    Args:
        msg: Error message.

    Returns:
        dict: ``{"error": msg}``.
    """
    return {"error": msg}


# --------------------------------------------------------------------------- #
# Tool schemas (sent to the model)
# --------------------------------------------------------------------------- #
get_stock_by_upc_schema = {
    "type": "function",
    "name": "get_stock_by_upc",
    "description": (
        "Return live stock levels for a product by its UPC barcode: good, damaged, "
        "reserved and available units at a warehouse. Use when asked how many of an "
        "item are in stock, whether an item is in stock, or current inventory."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "upc": {
                "type": "string",
                "description": "The product UPC barcode, e.g. '012345678905'.",
            },
            "warehouse_name": {
                "type": "string",
                "description": "Optional warehouse name ('Reno' or 'Columbus'). "
                "Omit to look across all warehouses.",
            },
        },
        "required": ["upc"],
    },
}

get_product_by_upc_schema = {
    "type": "function",
    "name": "get_product_by_upc",
    "description": (
        "Look up catalog details for a product by its UPC barcode: name, SKU, "
        "category, low-stock threshold, dimensions. Use to answer 'what is this item' "
        "or 'what is the low stock threshold'."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "upc": {"type": "string", "description": "The product UPC barcode."},
        },
        "required": ["upc"],
    },
}

get_low_stock_schema = {
    "type": "function",
    "name": "get_low_stock",
    "description": (
        "List products that are at or below their low-stock threshold at a warehouse. "
        "Use when asked which items are running low, need reordering, or are out of stock."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "warehouse_name": {
                "type": "string",
                "description": "Optional warehouse name. Omit to check all warehouses.",
            },
        },
    },
}

get_pending_orders_schema = {
    "type": "function",
    "name": "get_pending_orders",
    "description": (
        "List orders that are still pending, picking or packed (not yet shipped) at a "
        "warehouse. Use when asked which orders are pending, outstanding, or waiting to ship."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "warehouse_name": {
                "type": "string",
                "description": "Optional warehouse name. Omit to check all warehouses.",
            },
        },
    },
}

get_order_status_schema = {
    "type": "function",
    "name": "get_order_status",
    "description": (
        "Return the status, assigned staff, items and tracking of a single order by its "
        "reference (e.g. 'ORD-5521'). Use when asked about a specific order."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "order_ref": {"type": "string", "description": "The order reference, e.g. 'ORD-5521'."},
        },
        "required": ["order_ref"],
    },
}

get_bin_location_schema = {
    "type": "function",
    "name": "get_bin_location",
    "description": (
        "Find where a product is physically stored at a warehouse (aisle-row-shelf-bin). "
        "Use when asked 'where is X stored' or 'where do I put this'."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "product_name": {"type": "string", "description": "The product name, e.g. 'Widget A'."},
            "warehouse_name": {
                "type": "string",
                "description": "Optional warehouse name. Defaults to the first match.",
            },
        },
        "required": ["product_name"],
    },
}

get_shipment_status_schema = {
    "type": "function",
    "name": "get_shipment_status",
    "description": (
        "Return the status and received quantities of an inbound shipment by its "
        "reference/tracking number. Use when asked whether a shipment arrived or its status."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "shipment_ref": {"type": "string", "description": "The shipment/tracking reference."},
        },
        "required": ["shipment_ref"],
    },
}

get_damage_process_schema = {
    "type": "function",
    "name": "get_damage_process",
    "description": (
        "Explain the warehouse procedure for a damaged item by its damage grade (A, B, C, D). "
        "Use when asked what to do with a damaged item or what a grade means."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "grade": {
                "type": "string",
                "enum": ["A", "B", "C", "D"],
                "description": "The damage grade: A=minor, B=moderate, C=severe, D=total loss.",
            },
        },
        "required": ["grade"],
    },
}

get_inventory_summary_schema = {
    "type": "function",
    "name": "get_inventory_summary",
    "description": (
        "Count how many products (SKUs) are in the catalog and how many inventory records "
        "exist, optionally per warehouse. Use when asked 'how many products are there in "
        "the inventory', 'how many SKUs do we have', or a total/overview of the inventory."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "warehouse_name": {
                "type": "string",
                "description": "Optional warehouse name ('Reno' or 'Columbus'). Omit for the whole catalog.",
            },
        },
    },
}

get_orders_summary_schema = {
    "type": "function",
    "name": "get_orders_summary",
    "description": (
        "Count orders by status (pending, picking, packed, shipped, cancelled) and how many "
        "were shipped today, optionally per warehouse. Use when asked 'how many orders are "
        "there', 'how many orders today', or an order overview."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "warehouse_name": {
                "type": "string",
                "description": "Optional warehouse name. Omit for all warehouses.",
            },
        },
    },
}

get_total_units_in_stock_schema = {
    "type": "function",
    "name": "get_total_units_in_stock",
    "description": (
        "Return the total number of available units in stock, optionally per warehouse. "
        "Use when asked 'how many total units do we have', 'total stock', or 'how much "
        "inventory do we hold'."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "warehouse_name": {
                "type": "string",
                "description": "Optional warehouse name. Omit for all warehouses.",
            },
        },
    },
}

get_shipments_summary_schema = {
    "type": "function",
    "name": "get_shipments_summary",
    "description": (
        "Count inbound shipments by status (draft/received) and how many were received "
        "today, optionally per warehouse. Use when asked 'how many shipments', 'how many "
        "shipments received', or a shipment overview."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "warehouse_name": {
                "type": "string",
                "description": "Optional warehouse name. Omit for all warehouses.",
            },
        },
    },
}

get_seller_summary_schema = {
    "type": "function",
    "name": "get_seller_summary",
    "description": (
        "List the sellers and how many products each has in the catalog. Use when asked "
        "'how many sellers', 'which sellers do we have', or 'how many products does seller X have'."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "company_name": {
                "type": "string",
                "description": "Optional company name to filter to one seller.",
            },
        },
    },
}


# --------------------------------------------------------------------------- #
# Tool functions (what actually runs)
# --------------------------------------------------------------------------- #
async def get_stock_by_upc(upc: str, warehouse_name: str = "") -> Dict[str, Any]:
    """Return live stock for a product by UPC.

    Args:
        upc: Product UPC barcode.
        warehouse_name: Optional warehouse name.

    Returns:
        dict: Stock levels, or an error payload.
    """
    try:
        product = await collection("products").find_one({"upc_barcode": upc})
        if product is None:
            return _err(f"No product found with UPC {upc}")
        query: Dict[str, Any] = {"product_id": product["_id"]}
        wh_id = await _warehouse_id(warehouse_name)
        if wh_id:
            query["warehouse_id"] = wh_id
        rows = await collection("inventory").find(query).to_list(None)
        if not rows:
            return _err(f"No inventory recorded for {product.get('product_name')}")
        warehouses = {w["_id"]: w["name"] for w in await collection("warehouses").find({}).to_list(None)}
        result = []
        for row in rows:
            result.append(
                {
                    "warehouse": warehouses.get(row.get("warehouse_id"), "?"),
                    "quantity_good": row.get("quantity_good", 0),
                    "quantity_damaged": row.get("quantity_damaged", 0),
                    "quantity_reserved": row.get("quantity_reserved", 0),
                    "quantity_available": row.get("quantity_available", 0),
                    "bin_location": row.get("bin_location", ""),
                }
            )
        return {"product_name": product.get("product_name"), "upc": upc, "stock": result}
    except Exception as error:
        logging.error(f"Error in chatbot get_stock_by_upc: {error}")
        return _err(str(error))


async def get_product_by_upc(upc: str) -> Dict[str, Any]:
    """Return catalog details for a product by UPC.

    Args:
        upc: Product UPC barcode.

    Returns:
        dict: Product details, or an error payload.
    """
    try:
        product = await collection("products").find_one({"upc_barcode": upc})
        if product is None:
            return _err(f"No product found with UPC {upc}")
        return to_dict(product)
    except Exception as error:
        logging.error(f"Error in chatbot get_product_by_upc: {error}")
        return _err(str(error))


async def get_low_stock(warehouse_name: str = "") -> Dict[str, Any]:
    """List low-stock products.

    Args:
        warehouse_name: Optional warehouse name.

    Returns:
        dict: Low-stock products, or an error payload.
    """
    try:
        wh_id = await _warehouse_id(warehouse_name)
        query: Dict[str, Any] = {}
        if wh_id:
            query["warehouse_id"] = wh_id
        inventory = await collection("inventory").find(query).to_list(None)
        products = {p["_id"]: p for p in await collection("products").find({}).to_list(None)}
        warehouses = {w["_id"]: w["name"] for w in await collection("warehouses").find({}).to_list(None)}
        low = []
        for row in inventory:
            product = products.get(row.get("product_id"))
            if product is None:
                continue
            threshold = product.get("low_stock_threshold", 20)
            available = row.get("quantity_available", 0)
            if available <= threshold:
                low.append(
                    {
                        "product": product.get("product_name"),
                        "upc": product.get("upc_barcode"),
                        "warehouse": warehouses.get(row.get("warehouse_id"), "?"),
                        "available": available,
                        "low_stock_threshold": threshold,
                    }
                )
        low.sort(key=lambda x: x["available"])
        return {"low_stock_count": len(low), "items": low}
    except Exception as error:
        logging.error(f"Error in chatbot get_low_stock: {error}")
        return _err(str(error))


async def get_pending_orders(warehouse_name: str = "") -> Dict[str, Any]:
    """List pending/picking/packed orders.

    Args:
        warehouse_name: Optional warehouse name.

    Returns:
        dict: Pending orders, or an error payload.
    """
    try:
        wh_id = await _warehouse_id(warehouse_name)
        query: Dict[str, Any] = {"status": {"$in": ["pending", "picking", "packed"]}}
        if wh_id:
            query["warehouse_id"] = wh_id
        orders = await collection("orders").find(query).sort("created_at", -1).limit(20).to_list(None)
        warehouses = {w["_id"]: w["name"] for w in await collection("warehouses").find({}).to_list(None)}
        return {
            "pending_count": len(orders),
            "orders": [
                {
                    "order_ref": o.get("order_ref"),
                    "status": o.get("status"),
                    "warehouse": warehouses.get(o.get("warehouse_id"), "?"),
                    "customer": (o.get("customer") or {}).get("name"),
                }
                for o in orders
            ],
        }
    except Exception as error:
        logging.error(f"Error in chatbot get_pending_orders: {error}")
        return _err(str(error))


async def get_order_status(order_ref: str) -> Dict[str, Any]:
    """Return the status of a single order.

    Args:
        order_ref: Order reference (e.g. 'ORD-5521').

    Returns:
        dict: Order details, or an error payload.
    """
    try:
        order = await collection("orders").find_one({"order_ref": order_ref})
        if order is None:
            return _err(f"No order found with reference {order_ref}")
        warehouses = {w["_id"]: w["name"] for w in await collection("warehouses").find({}).to_list(None)}
        return {
            "order_ref": order.get("order_ref"),
            "status": order.get("status"),
            "warehouse": warehouses.get(order.get("warehouse_id"), "?"),
            "assigned_to": str(order.get("assigned_to")) if order.get("assigned_to") else None,
            "items": [
                {
                    "product": i.get("product_name"),
                    "quantity": i.get("quantity"),
                }
                for i in order.get("items", [])
            ],
            "shipping": order.get("shipping"),
        }
    except Exception as error:
        logging.error(f"Error in chatbot get_order_status: {error}")
        return _err(str(error))


async def get_bin_location(product_name: str, warehouse_name: str = "") -> Dict[str, Any]:
    """Find where a product is stored.

    Args:
        product_name: Product name.
        warehouse_name: Optional warehouse name.

    Returns:
        dict: Bin location, or an error payload.
    """
    try:
        product = await collection("products").find_one(
            {"product_name": {"$regex": f"^{product_name}$", "$options": "i"}}
        )
        if product is None:
            return _err(f"No product found named {product_name}")
        wh_id = await _warehouse_id(warehouse_name)
        query: Dict[str, Any] = {"product_id": product["_id"]}
        if wh_id:
            query["warehouse_id"] = wh_id
        bin_row = await collection("bin_locations").find_one(query)
        if bin_row is None:
            return _err(f"No bin location assigned for {product.get('product_name')}")
        warehouses = {w["_id"]: w["name"] for w in await collection("warehouses").find({}).to_list(None)}
        return {
            "product": product.get("product_name"),
            "warehouse": warehouses.get(bin_row.get("warehouse_id"), "?"),
            "bin_code": bin_row.get("bin_code"),
            "current_units": bin_row.get("current_units", 0),
        }
    except Exception as error:
        logging.error(f"Error in chatbot get_bin_location: {error}")
        return _err(str(error))


async def get_shipment_status(shipment_ref: str) -> Dict[str, Any]:
    """Return the status of an inbound shipment.

    Args:
        shipment_ref: Shipment/tracking reference.

    Returns:
        dict: Shipment details, or an error payload.
    """
    try:
        shipment = await collection("shipments").find_one({"shipment_ref": shipment_ref})
        if shipment is None:
            return _err(f"No shipment found with reference {shipment_ref}")
        return {
            "shipment_ref": shipment.get("shipment_ref"),
            "status": shipment.get("status"),
            "received_at": shipment.get("received_at"),
            "carrier": shipment.get("carrier"),
            "items": [
                {
                    "product": i.get("product_name"),
                    "expected": i.get("quantity_expected"),
                    "received": i.get("quantity_received"),
                    "damaged": i.get("quantity_damaged"),
                }
                for i in shipment.get("items", [])
            ],
        }
    except Exception as error:
        logging.error(f"Error in chatbot get_shipment_status: {error}")
        return _err(str(error))


async def get_inventory_summary(warehouse_name: str = "") -> Dict[str, Any]:
    """Count products in the catalog and inventory records.

    Args:
        warehouse_name: Optional warehouse name to narrow the count.

    Returns:
        dict: Product/inventory counts, or an error payload.
    """
    try:
        # The catalog size is the same regardless of warehouse filter — counting
        # products is a whole-catalog question. The warehouse filter only narrows
        # the inventory-record count below.
        total_products = await collection("products").count_documents({})

        # Count inventory records (optionally filtered to a warehouse).
        inv_query: Dict[str, Any] = {}
        if warehouse_name:
            wh_id = await _warehouse_id(warehouse_name)
            if wh_id is None:
                return _err(f"Warehouse '{warehouse_name}' not found")
            inv_query["warehouse_id"] = wh_id
        total_inventory_records = await collection("inventory").count_documents(inv_query)

        # Per-warehouse breakdown (only when not already filtered to one warehouse).
        warehouses = {w["_id"]: w["name"] for w in await collection("warehouses").find({}).to_list(None)}
        per_warehouse = []
        if not warehouse_name:
            for wh_id, wh_name in warehouses.items():
                count = await collection("inventory").count_documents({"warehouse_id": wh_id})
                per_warehouse.append({"warehouse": wh_name, "inventory_records": count})

        return {
            "total_products": total_products,
            "total_inventory_records": total_inventory_records,
            "filtered_to_warehouse": warehouse_name or None,
            "per_warehouse": per_warehouse,
        }
    except Exception as error:
        logging.error(f"Error in chatbot get_inventory_summary: {error}")
        return _err(str(error))


async def get_orders_summary(warehouse_name: str = "") -> Dict[str, Any]:
    """Count orders by status, optionally per warehouse.

    Args:
        warehouse_name: Optional warehouse name.

    Returns:
        dict: Order counts, or an error payload.
    """
    try:
        wh_id = await _warehouse_id(warehouse_name)
        if warehouse_name and wh_id is None:
            return _err(f"Warehouse '{warehouse_name}' not found")
        query: Dict[str, Any] = {}
        if wh_id:
            query["warehouse_id"] = wh_id

        statuses = ["pending", "picking", "packed", "labeled", "shipped", "cancelled"]
        by_status = {}
        for st in statuses:
            by_status[st] = await collection("orders").count_documents({**query, "status": st})

        # Orders shipped today (match on date prefix of shipped_at).
        from datetime import datetime, timezone

        today = datetime.now(timezone.utc).isoformat()[:10]
        ship_query = {
            **query,
            "status": "shipped",
            "shipping.shipped_at": {"$regex": f"^{today}"},
        }
        shipped_today = await collection("orders").count_documents(ship_query)

        return {
            "filtered_to_warehouse": warehouse_name or None,
            "by_status": by_status,
            "shipped_today": shipped_today,
            "total": sum(by_status.values()),
        }
    except Exception as error:
        logging.error(f"Error in chatbot get_orders_summary: {error}")
        return _err(str(error))


async def get_total_units_in_stock(warehouse_name: str = "") -> Dict[str, Any]:
    """Sum available stock units, optionally per warehouse.

    Args:
        warehouse_name: Optional warehouse name.

    Returns:
        dict: Total units and per-warehouse breakdown, or an error payload.
    """
    try:
        wh_id = await _warehouse_id(warehouse_name)
        if warehouse_name and wh_id is None:
            return _err(f"Warehouse '{warehouse_name}' not found")
        match: Dict[str, Any] = {}
        if wh_id:
            match["warehouse_id"] = wh_id

        pipeline = [{"$match": match}, {"$group": {"_id": None, "total": {"$sum": "$quantity_available"}}}]
        rows = await collection("inventory").aggregate(pipeline).to_list(None)
        total = rows[0]["total"] if rows else 0

        per_warehouse = []
        if not warehouse_name:
            warehouses = {w["_id"]: w["name"] for w in await collection("warehouses").find({}).to_list(None)}
            for wh_id_i, wh_name in warehouses.items():
                rows_i = (
                    await collection("inventory")
                    .aggregate(
                        [
                            {"$match": {"warehouse_id": wh_id_i}},
                            {"$group": {"_id": None, "total": {"$sum": "$quantity_available"}}},
                        ]
                    )
                    .to_list(None)
                )
                per_warehouse.append({"warehouse": wh_name, "available_units": rows_i[0]["total"] if rows_i else 0})

        return {"total_available_units": total, "filtered_to_warehouse": warehouse_name or None, "per_warehouse": per_warehouse}
    except Exception as error:
        logging.error(f"Error in chatbot get_total_units_in_stock: {error}")
        return _err(str(error))


async def get_shipments_summary(warehouse_name: str = "") -> Dict[str, Any]:
    """Count inbound shipments by status, optionally per warehouse.

    Args:
        warehouse_name: Optional warehouse name.

    Returns:
        dict: Shipment counts, or an error payload.
    """
    try:
        wh_id = await _warehouse_id(warehouse_name)
        if warehouse_name and wh_id is None:
            return _err(f"Warehouse '{warehouse_name}' not found")
        query: Dict[str, Any] = {}
        if wh_id:
            query["warehouse_id"] = wh_id

        drafts = await collection("shipments").count_documents({**query, "status": "draft"})
        received = await collection("shipments").count_documents({**query, "status": "received"})

        from datetime import datetime, timezone

        today = datetime.now(timezone.utc).isoformat()[:10]
        received_today = await collection("shipments").count_documents(
            {**query, "status": "received", "received_at": {"$regex": f"^{today}"}}
        )

        return {
            "filtered_to_warehouse": warehouse_name or None,
            "draft": drafts,
            "received": received,
            "received_today": received_today,
            "total": drafts + received,
        }
    except Exception as error:
        logging.error(f"Error in chatbot get_shipments_summary: {error}")
        return _err(str(error))


async def get_seller_summary(company_name: str = "") -> Dict[str, Any]:
    """List sellers and their product counts.

    Args:
        company_name: Optional company name to filter to one seller.

    Returns:
        dict: Seller/product counts, or an error payload.
    """
    try:
        sellers = await collection("sellers").find({}).to_list(None)
        products = await collection("products").find({}).to_list(None)
        count_by_seller: Dict[str, int] = {}
        for p in products:
            key = str(p.get("seller_id"))
            count_by_seller[key] = count_by_seller.get(key, 0) + 1

        result = []
        for s in sellers:
            if company_name and s.get("company_name", "").lower() != company_name.lower():
                continue
            result.append(
                {
                    "company_name": s.get("company_name"),
                    "contact_name": s.get("contact_name"),
                    "product_count": count_by_seller.get(str(s.get("_id")), 0),
                }
            )

        if company_name and not result:
            return _err(f"No seller found named {company_name}")
        return {"total_sellers": len(result), "sellers": result}
    except Exception as error:
        logging.error(f"Error in chatbot get_seller_summary: {error}")
        return _err(str(error))


# Damage grading knowledge base (from the case study).
DAMAGE_PROCESS = {
    "A": (
        "Grade A = minor damage (small dents/marks on outer packaging, product is fine). "
        "It is still sellable as new: move it back to good stock after inspection. "
        "A seller notification is sent for information only."
    ),
    "B": (
        "Grade B = moderate damage (packaging torn/crushed, minor cosmetic issues possible). "
        "It is sellable at a discount: place it in the discounted stock zone. "
        "A seller notification is sent and the seller decides the discount price."
    ),
    "C": (
        "Grade C = severe damage (the product itself is damaged and cannot be sold). "
        "Hold it in the Grade C zone for seller instructions. The seller is notified "
        "urgently with full details, then either returned to the seller or disposed "
        "per their instructions."
    ),
    "D": (
        "Grade D = total loss (product completely destroyed, unsalvageable). "
        "A carrier claim is initiated automatically, and the seller is notified "
        "immediately with the claim details."
    ),
}


async def get_damage_process(grade: str) -> Dict[str, Any]:
    """Explain the procedure for a damage grade.

    Args:
        grade: Damage grade (A/B/C/D).

    Returns:
        dict: Process explanation, or an error payload.
    """
    grade = grade.upper()
    explanation = DAMAGE_PROCESS.get(grade)
    if explanation is None:
        return _err(f"'{grade}' is not a valid damage grade. Valid grades are A, B, C, D.")
    return {"grade": grade, "procedure": explanation}


# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #
TOOLS = [
    get_stock_by_upc_schema,
    get_product_by_upc_schema,
    get_low_stock_schema,
    get_pending_orders_schema,
    get_order_status_schema,
    get_bin_location_schema,
    get_shipment_status_schema,
    get_damage_process_schema,
    get_inventory_summary_schema,
    get_orders_summary_schema,
    get_total_units_in_stock_schema,
    get_shipments_summary_schema,
    get_seller_summary_schema,
]

FUNCTIONS = {
    "get_stock_by_upc": get_stock_by_upc,
    "get_product_by_upc": get_product_by_upc,
    "get_low_stock": get_low_stock,
    "get_pending_orders": get_pending_orders,
    "get_order_status": get_order_status,
    "get_bin_location": get_bin_location,
    "get_shipment_status": get_shipment_status,
    "get_damage_process": get_damage_process,
    "get_inventory_summary": get_inventory_summary,
    "get_orders_summary": get_orders_summary,
    "get_total_units_in_stock": get_total_units_in_stock,
    "get_shipments_summary": get_shipments_summary,
    "get_seller_summary": get_seller_summary,
}


async def run_tool(name: str, arguments: dict) -> Dict[str, Any]:
    """Run a tool by name with its arguments.

    Args:
        name: Tool name (must match a key in FUNCTIONS).
        arguments: Tool arguments.

    Returns:
        dict: The tool result, or an error payload.
    """
    function = FUNCTIONS.get(name)
    if function is None:
        return _err(f"There is no tool called '{name}'.")
    try:
        return await function(**arguments)
    except Exception as error:
        logging.error(f"Error running chatbot tool {name}: {error}")
        return _err(str(error))

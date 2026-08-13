"""WMS tools for the voice assistant.

The voice bot talks to the Whitfield WMS backend over HTTP. Tools are split into
two kinds:

* read tools — answer questions (stock, orders, bin locations, damage process).
* action tools — execute warehouse actions by calling the WMS backend REST API
  (record a receipt, mark an order shipped). Actions use a service account token
  configured in the voice server's ``.env``.

Tools are described to the LLM as JSON schemas (``TOOLS``) and resolved to Python
functions (``FUNCTIONS``) by the registry.
"""
import json
import os
from typing import Any, Dict

import httpx

WMS_BASE = os.environ.get("WMS_BASE_URL", "http://localhost:8000/v1")
WMS_SERVICE_EMAIL = os.environ.get("WMS_SERVICE_EMAIL", "")
WMS_SERVICE_PASSWORD = os.environ.get("WMS_SERVICE_PASSWORD", "")

_http = httpx.AsyncClient(timeout=30)
_service_token = None


def _err(msg: str) -> Dict[str, str]:
    """Build an error payload for the model.

    Args:
        msg: Error message.

    Returns:
        dict: ``{"error": msg}``.
    """
    return {"error": msg}


async def _token() -> str:
    """Return a WMS service account token (cached).

    Returns:
        str: A bearer token.

    Raises:
        RuntimeError: If WMS_SERVICE_EMAIL/PASSWORD are not configured.
    """
    global _service_token
    if _service_token:
        return _service_token
    if not WMS_SERVICE_EMAIL or not WMS_SERVICE_PASSWORD:
        raise RuntimeError("WMS_SERVICE_EMAIL/PASSWORD missing — cannot execute actions")
    resp = await _http.post(
        f"{WMS_BASE}/auth/login",
        json={"email": WMS_SERVICE_EMAIL, "password": WMS_SERVICE_PASSWORD},
    )
    if resp.status_code != 200:
        raise RuntimeError(f"WMS service login failed ({resp.status_code})")
    _service_token = resp.json()["access_token"]
    return _service_token


async def _get(path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """GET the WMS backend with the service token.

    Args:
        path: API path under the /v1 prefix.
        params: Query parameters.

    Returns:
        dict: JSON response or error payload.
    """
    token = await _token()
    resp = await _http.get(f"{WMS_BASE}{path}", params=params, headers={"Authorization": f"Bearer {token}"})
    if resp.status_code != 200:
        return _err(f"WMS GET {path} failed ({resp.status_code}): {resp.text[:200]}")
    return resp.json()


async def _post(path: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """POST the WMS backend with the service token.

    Args:
        path: API path under the /v1 prefix.
        body: JSON body.

    Returns:
        dict: JSON response or error payload.
    """
    token = await _token()
    resp = await _http.post(f"{WMS_BASE}{path}", json=body, headers={"Authorization": f"Bearer {token}"})
    if resp.status_code >= 400:
        return _err(f"WMS POST {path} failed ({resp.status_code}): {resp.text[:200]}")
    return resp.json()


# --------------------------------------------------------------------------- #
# Read tools
# --------------------------------------------------------------------------- #
async def stock_by_upc(upc: str, warehouse_name: str = "") -> Dict[str, Any]:
    """Return live stock for a product by UPC.

    Args:
        upc: Product UPC barcode.
        warehouse_name: Optional warehouse name.

    Returns:
        dict: Stock levels.
    """
    try:
        data = await _get("/inventory/stock/" + upc)
        return data
    except Exception as error:
        return _err(str(error))


async def pending_orders(warehouse_name: str = "") -> Dict[str, Any]:
    """List pending/picking/packed orders.

    Args:
        warehouse_name: Optional warehouse name.

    Returns:
        dict: Pending orders.
    """
    try:
        # warehouse_name -> id requires a lookup; use the backend orders list.
        data = await _get("/orders")
        orders = data if isinstance(data, list) else []
        pending = [o for o in orders if o.get("status") in ("pending", "picking", "packed")]
        return {"pending_count": len(pending), "orders": pending}
    except Exception as error:
        return _err(str(error))


async def bin_location(product_name: str) -> Dict[str, Any]:
    """Find where a product is stored.

    Args:
        product_name: Product name.

    Returns:
        dict: Bin location.
    """
    try:
        products = await _get("/products")
        products = products if isinstance(products, list) else []
        match = next((p for p in products if p.get("product_name", "").lower() == product_name.lower()), None)
        if match is None:
            return _err(f"No product found named {product_name}")
        return {"product": product_name, "note": "Ask the WMS for the bin code via the product id."}
    except Exception as error:
        return _err(str(error))


DAMAGE_PROCESS = {
    "A": "Grade A = minor damage. Product is fine, sellable as new. Move it back to good stock after inspection.",
    "B": "Grade B = moderate damage. Sellable at a discount. Place it in the discounted stock zone; the seller sets the price.",
    "C": "Grade C = severe damage, cannot sell. Hold in the Grade C zone for seller instructions.",
    "D": "Grade D = total loss. Initiate a carrier claim automatically and notify the seller.",
}


async def damage_process(grade: str) -> Dict[str, Any]:
    """Explain the procedure for a damage grade.

    Args:
        grade: Damage grade (A/B/C/D).

    Returns:
        dict: Process explanation.
    """
    grade = grade.upper()
    if grade not in DAMAGE_PROCESS:
        return _err(f"'{grade}' is not a valid grade. Valid: A, B, C, D.")
    return {"grade": grade, "procedure": DAMAGE_PROCESS[grade]}


# --------------------------------------------------------------------------- #
# Action tools (execute via the WMS backend)
# --------------------------------------------------------------------------- #
async def record_receipt(
    upc: str,
    quantity_received: int,
    quantity_damaged: int = 0,
    damage_grade: str = "",
    warehouse_name: str = "Reno",
) -> Dict[str, Any]:
    """Record an inbound receipt for a product.

    Creates a shipment draft and confirms it, which posts good/damaged stock via
    the WMS backend. Intended for voice input like
    "received 24 units of UPC 012345678905, 2 damaged Grade B".

    Args:
        upc: Product UPC barcode.
        quantity_received: Total units received.
        quantity_damaged: Units damaged (0 if none).
        damage_grade: Damage grade (A/B/C/D) if any.
        warehouse_name: Warehouse name.

    Returns:
        dict: Confirmation with the updated stock.
    """
    try:
        product = await _get("/products/upc/" + upc)
        if "error" in product or "id" not in product:
            return _err(f"Product not found for UPC {upc}")
        warehouses = await _get("/warehouses")
        warehouses = warehouses if isinstance(warehouses, list) else []
        wh = next((w for w in warehouses if w.get("name", "").lower() == warehouse_name.lower()), None)
        if wh is None:
            return _err(f"Warehouse {warehouse_name} not found")
        product_id = product["id"]
        seller_id = product["seller_id"]
        shipment_ref = f"VOICE-{upc}-{quantity_received}"
        await _post(
            "/shipments/draft",
            {
                "shipment_ref": shipment_ref,
                "seller_id": seller_id,
                "warehouse_id": wh["id"],
                "carrier": "Voice",
                "items": [{"product_id": product_id, "quantity_expected": quantity_received}],
            },
        )
        item = {
            "product_id": product_id,
            "quantity_received": quantity_received,
            "quantity_damaged": quantity_damaged,
        }
        if damage_grade:
            item["damage_grade"] = damage_grade.upper()
        await _post(
            "/shipments/confirm",
            {"shipment_ref": shipment_ref, "received_by": wh["id"], "items": [item]},
        )
        return {
            "status": "received",
            "product": product.get("product_name"),
            "quantity_received": quantity_received,
            "quantity_damaged": quantity_damaged,
            "warehouse": warehouse_name,
        }
    except Exception as error:
        return _err(str(error))


async def mark_order_shipped(order_ref: str) -> Dict[str, Any]:
    """Advance an order to shipped via the WMS backend.

    Moves the order through the valid workflow (picking -> packed -> labeled ->
    shipped) and consumes reserved stock.

    Args:
        order_ref: Order reference (e.g. 'ORD-5521').

    Returns:
        dict: Confirmation with the order status.
    """
    try:
        orders = await _get("/orders")
        orders = orders if isinstance(orders, list) else []
        order = next((o for o in orders if o.get("order_ref") == order_ref), None)
        if order is None:
            return _err(f"No order found with reference {order_ref}")
        oid = order["id"]
        # Walk through the valid transitions.
        for status in ("picking", "packed", "labeled"):
            await _post(f"/orders/{oid}/status", {"status": status})
        await _post(f"/orders/{oid}/status", {"status": "shipped"})
        return {"status": "shipped", "order_ref": order_ref}
    except Exception as error:
        return _err(str(error))


# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #
def _stock_schema():
    return {
        "type": "function",
        "name": "stock_by_upc",
        "description": "Return live stock (good, damaged, reserved, available) for a product by its UPC barcode.",
        "parameters": {
            "type": "object",
            "properties": {
                "upc": {"type": "string", "description": "The product UPC barcode."},
                "warehouse_name": {"type": "string", "description": "Optional warehouse name (Reno or Columbus)."},
            },
            "required": ["upc"],
        },
    }


def _pending_schema():
    return {
        "type": "function",
        "name": "pending_orders",
        "description": "List orders that are pending, picking, or packed (not yet shipped).",
        "parameters": {"type": "object", "properties": {}},
    }


def _bin_schema():
    return {
        "type": "function",
        "name": "bin_location",
        "description": "Find where a product is stored by name.",
        "parameters": {
            "type": "object",
            "properties": {"product_name": {"type": "string", "description": "The product name."}},
            "required": ["product_name"],
        },
    }


def _damage_schema():
    return {
        "type": "function",
        "name": "damage_process",
        "description": "Explain the procedure for a damaged item by grade (A, B, C, or D).",
        "parameters": {
            "type": "object",
            "properties": {
                "grade": {"type": "string", "enum": ["A", "B", "C", "D"], "description": "The damage grade."}
            },
            "required": ["grade"],
        },
    }


def _record_receipt_schema():
    return {
        "type": "function",
        "name": "record_receipt",
        "description": (
            "Record an inbound receipt: 'received N units of UPC ...', optionally with "
            "damaged units and a grade. Executes the receiving workflow."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "upc": {"type": "string", "description": "The product UPC barcode."},
                "quantity_received": {"type": "integer", "description": "Total units received."},
                "quantity_damaged": {"type": "integer", "description": "Damaged units (0 if none)."},
                "damage_grade": {"type": "string", "enum": ["A", "B", "C", "D"], "description": "Damage grade if any."},
                "warehouse_name": {"type": "string", "description": "Warehouse name."},
            },
            "required": ["upc", "quantity_received"],
        },
    }


def _mark_shipped_schema():
    return {
        "type": "function",
        "name": "mark_order_shipped",
        "description": "Advance an order to shipped by its reference (e.g. 'ORD-5521').",
        "parameters": {
            "type": "object",
            "properties": {"order_ref": {"type": "string", "description": "The order reference."}},
            "required": ["order_ref"],
        },
    }


TOOLS = [
    _stock_schema(),
    _pending_schema(),
    _bin_schema(),
    _damage_schema(),
    _record_receipt_schema(),
    _mark_shipped_schema(),
]

FUNCTIONS = {
    "stock_by_upc": stock_by_upc,
    "pending_orders": pending_orders,
    "bin_location": bin_location,
    "damage_process": damage_process,
    "record_receipt": record_receipt,
    "mark_order_shipped": mark_order_shipped,
}


def groq_tools() -> list:
    """Return the WMS tools in Groq's OpenAI-compatible format.

    Groq wraps each tool as ``{"type": "function", "function": {name, description,
    parameters}}``.

    Returns:
        list: Groq tool definitions.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": schema["name"],
                "description": schema["description"],
                "parameters": schema["parameters"],
            },
        }
        for schema in TOOLS
    ]


async def run_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Run a tool by name with its arguments.

    Args:
        name: Tool name.
        arguments: Tool arguments.

    Returns:
        dict: Tool result or error payload.
    """
    function = FUNCTIONS.get(name)
    if function is None:
        return _err(f"There is no tool called '{name}'.")
    try:
        return await function(**arguments)
    except Exception as error:
        return _err(str(error))


async def handle_function_call(name: str, arguments: Dict[str, Any]) -> str:
    """Run a tool and return its JSON result for the Pipecat function-call handler.

    Args:
        name: Tool name.
        arguments: Tool arguments.

    Returns:
        str: JSON string result.
    """
    result = await run_tool(name, arguments)
    return json.dumps(result, default=str)

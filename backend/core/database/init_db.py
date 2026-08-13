"""Database initialization — indexes and safe startup seed records.

Runs at application startup. Creating the indexes here enforces the case study's
data-integrity guarantees (unique shipment/product/email references, compound
inventory uniqueness, audit lookup indexes).
"""
from typing import List, Tuple

from bson import ObjectId

from commons.auth import hash_password
from core import logger
from core.database.database import collection
from core.models.enums import UserRole

logging = logger(__name__)

# List of (collection, list of (keys, kwargs)) index definitions.
INDEXES: List[Tuple[str, List[Tuple[dict, dict]]]] = [
    ("users", [({"email": 1}, {"unique": True}), ({"warehouse_id": 1}, {}), ({"role": 1}, {})]),
    ("warehouses", [({"name": 1}, {"unique": True})]),
    ("sellers", [({"email": 1}, {"unique": True}), ({"company_name": 1}, {})]),
    ("products", [({"upc_barcode": 1}, {"unique": True}), ({"seller_id": 1}, {}), ({"sku": 1}, {})]),
    (
        "inventory",
        [
            ({"product_id": 1, "warehouse_id": 1}, {"unique": True}),
            ({"seller_id": 1}, {}),
            ({"quantity_available": 1}, {}),
        ],
    ),
    (
        "shipments",
        [
            ({"shipment_ref": 1}, {"unique": True}),
            ({"warehouse_id": 1}, {}),
            ({"seller_id": 1}, {}),
            ({"received_at": -1}, {}),
        ],
    ),
    (
        "orders",
        [
            ({"order_ref": 1}, {"unique": True}),
            ({"status": 1}, {}),
            ({"warehouse_id": 1, "status": 1}, {}),
            ({"seller_id": 1}, {}),
            ({"assigned_to": 1}, {}),
        ],
    ),
    (
        "audit_logs",
        [
            ({"record_id": 1}, {}),
            ({"user_id": 1}, {}),
            ({"created_at": -1}, {}),
            ({"warehouse_id": 1}, {}),
        ],
    ),
    (
        "damage_records",
        [
            ({"shipment_id": 1}, {}),
            ({"carrier": 1}, {}),
            ({"damage_grade": 1}, {}),
            ({"seller_id": 1}, {}),
        ],
    ),
    (
        "bin_locations",
        [
            ({"bin_code": 1, "warehouse_id": 1}, {"unique": True}),
            ({"product_id": 1}, {}),
        ],
    ),
    (
        "returns",
        [
            ({"return_ref": 1}, {"unique": True}),
            ({"original_order_id": 1}, {}),
            ({"seller_id": 1}, {}),
        ],
    ),
    (
        "invoices",
        [
            ({"invoice_ref": 1}, {"unique": True}),
            ({"seller_id": 1, "period.year": 1, "period.month": 1}, {}),
        ],
    ),
    (
        "forecasts",
        [
            ({"product_id": 1}, {}),
            ({"seller_id": 1}, {}),
            ({"days_remaining": 1}, {}),
            ({"calculated_at": -1}, {}),
        ],
    ),
    (
        "notifications",
        [
            ({"recipient_id": 1}, {}),
            ({"is_read": 1}, {}),
            ({"created_at": -1}, {}),
        ],
    ),
]


async def create_indexes() -> None:
    """Create all application indexes idempotently.

    Raises:
        Exception: If any index creation fails.
    """
    try:
        for coll_name, index_specs in INDEXES:
            coll = collection(coll_name)
            for keys, kwargs in index_specs:
                await coll.create_index(list(keys.items()), **kwargs)
        logging.info("All MongoDB indexes verified/created")
    except Exception as error:
        logging.error(f"Failed to create indexes: {error}")
        raise


async def seed_default_data() -> None:
    """Insert minimal seed records if the database is empty.

    Creates the two warehouses and a default admin user. Uses ``update_one`` with
    upsert so seeding is idempotent. Passwords are bcrypt-hashed.

    Raises:
        Exception: If any seed write fails.
    """
    try:
        warehouses = collection("warehouses")
        reno_id = await _ensure_warehouse(warehouses, "Reno", "Reno", "Nevada")
        columbus_id = await _ensure_warehouse(warehouses, "Columbus", "Columbus", "Ohio")

        users = collection("users")
        existing = await users.find_one({"email": "dan@whitfieldfulfillment.com"})
        if existing is None:
            await users.insert_one(
                {
                    "full_name": "Dan Whitfield",
                    "email": "dan@whitfieldfulfillment.com",
                    "password_hash": hash_password("admin123"),
                    "role": UserRole.ADMIN.value,
                    "warehouse_id": reno_id,
                    "is_active": True,
                }
            )
            logging.info("Seeded default admin user")
    except Exception as error:
        logging.error(f"Failed to seed default data: {error}")
        raise


async def _ensure_warehouse(coll, name: str, city: str, state: str) -> ObjectId:
    """Upsert a warehouse and return its id.

    Args:
        coll: Warehouses collection.
        name: Warehouse name.
        city: Warehouse city.
        state: Warehouse state.

    Returns:
        ObjectId: The warehouse document id.
    """
    doc = await coll.find_one({"name": name})
    if doc is None:
        result = await coll.insert_one(
            {
                "name": name,
                "city": city,
                "state": state,
                "address": f"{name} Warehouse",
                "is_active": True,
            }
        )
        return result.inserted_id
    return doc["_id"]

"""Role-based access control helpers used by controllers.

Encodes the case study's role permissions as readable data structures.
"""
from typing import Any, List, Optional

from fastapi import HTTPException, status


class RolePolicy:
    """Permission sets per role."""

    # collections a role may read
    READ: dict = {
        "admin": "*",
        "manager": "*",
        # staff = receiver + picker combined (inbound receiving and outbound picking)
        "staff": ["inventory", "products", "bin_locations", "orders"],
        "seller": ["inventory", "shipments", "orders", "returns", "invoices", "forecasts"],
    }
    # collections a role may write
    WRITE: dict = {
        "admin": "*",
        "manager": ["inventory", "orders", "shipments", "damage_records", "returns", "bin_locations"],
        # staff can receive shipments/damage and update order status + bin locations
        "staff": ["shipments", "damage_records", "bin_locations", "orders"],
        "seller": [],
    }
    # collections a role may delete
    DELETE: dict = {
        "admin": ["users", "warehouses", "sellers", "products", "inventory", "shipments", "orders", "damage_records", "bin_locations", "returns", "notifications"],
        "manager": [],
        "staff": [],
        "seller": [],
    }
    # collections a role may never touch (read or write)
    FORBIDDEN: dict = {
        "staff": ["invoices", "users", "audit_logs"],
        "seller": ["users", "audit_logs", "damage_records", "warehouses"],
    }


def _allowed(permissions, role: str, collection_name: str) -> bool:
    """Return whether a role may operate on a collection under a permission set.

    Args:
        permissions: The permission mapping (READ/WRITE/DELETE).
        role: The user's role.
        collection_name: The target collection.

    Returns:
        bool: True if allowed.
    """
    allowed = permissions.get(role, [])
    if allowed == "*":
        return True
    return collection_name in allowed


def check_read(role: str, collection_name: str) -> None:
    """Raise 403 if a role cannot read a collection.

    Args:
        role: The user's role.
        collection_name: The target collection.

    Raises:
        HTTPException 403: If access is forbidden.
    """
    if collection_name in RolePolicy.FORBIDDEN.get(role, []):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if not _allowed(RolePolicy.READ, role, collection_name):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


def check_write(role: str, collection_name: str) -> None:
    """Raise 403 if a role cannot write to a collection.

    Args:
        role: The user's role.
        collection_name: The target collection.

    Raises:
        HTTPException 403: If access is forbidden.
    """
    if collection_name in RolePolicy.FORBIDDEN.get(role, []):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if not _allowed(RolePolicy.WRITE, role, collection_name):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


def check_delete(role: str, collection_name: str) -> None:
    """Raise 403 if a role cannot delete from a collection.

    Args:
        role: The user's role.
        collection_name: The target collection.

    Raises:
        HTTPException 403: If access is forbidden.
    """
    if not _allowed(RolePolicy.DELETE, role, collection_name):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


def require_roles(role: str, allowed: List[str]) -> None:
    """Raise 403 if the user's role is not in the allowed set.

    Args:
        role: The user's role.
        allowed: Allowed roles.

    Raises:
        HTTPException 403: If the role is not allowed.
    """
    if role not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


def same_warehouse(user_wh: Optional[Any], record_wh: Optional[Any]) -> bool:
    """Return whether a user's warehouse matches a record's warehouse.

    Args:
        user_wh: User warehouse id.
        record_wh: Record warehouse id.

    Returns:
        bool: True if both are set and equal.
    """
    return bool(user_wh) and bool(record_wh) and str(user_wh) == str(record_wh)

"""Damage record persistence operations."""
from core.cruds.base_crud import BaseCRUD


class CRUDDamageRecord(BaseCRUD):
    """Database access layer for damage records."""

    COLLECTION_NAME = "damage_records"

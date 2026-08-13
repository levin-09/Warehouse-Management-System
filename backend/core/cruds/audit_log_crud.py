"""Audit log persistence operations.

This CRUD intentionally exposes insert and read only. There is no update or delete
method so the audit trail cannot be modified through the application layer.
"""
from typing import Any, Dict, List

from core.cruds.base_crud import BaseCRUD


class CRUDAuditLog(BaseCRUD):
    """Database access layer for audit log records (insert-only)."""

    COLLECTION_NAME = "audit_logs"

    async def create(self, *, obj_in: dict) -> Dict[str, Any]:
        """Insert an audit log entry.

        Args:
            obj_in: Audit log data.

        Returns:
            dict: The created audit log document.
        """
        return await super().create(obj_in=obj_in)

    async def history(self, *, record_id: Any, collection_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Return the audit history for a record, newest first.

        Args:
            record_id: Record id.
            collection_name: Collection the record belongs to.
            limit: Maximum entries.

        Returns:
            List[dict]: Audit entries sorted by created_at descending.
        """
        cursor = self.coll.find(
            {"record_id": record_id, "collection_name": collection_name}
        ).sort("created_at", -1).limit(limit)
        return [doc async for doc in cursor]

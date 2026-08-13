"""Audit log controller — read-only access to the immutable audit trail."""
from typing import Any, Dict, List

from bson import ObjectId
from fastapi import HTTPException, status

from core import logger
from core.cruds.audit_log_crud import CRUDAuditLog
from core.models.enums import UserRole
from core.utils.custom.database_helper import to_dict
from core.utils.rbac import require_roles

logging = logger(__name__)


class AuditLogController:
    """Exposes read-only queries over audit logs (admin only)."""

    def __init__(self) -> None:
        """Initialize the audit CRUD."""
        self.CRUDAudit = CRUDAuditLog()

    async def list(self, auth: Dict[str, Any], record_id: str = "", limit: int = 50) -> List[dict]:
        """List audit log entries.

        Args:
            auth: Authenticated user.
            record_id: Optional record id filter.
            limit: Max entries.

        Returns:
            List[dict]: Audit log payloads.

        Raises:
            HTTPException 403: Not admin.
        """
        try:
            logging.info("Executing AuditLogController.list")
            require_roles(auth["role"], [UserRole.ADMIN.value])
            query: Dict[str, Any] = {}
            if record_id:
                if not ObjectId.is_valid(record_id):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="record_id must be a valid ObjectId",
                    )
                query["record_id"] = ObjectId(record_id)
            logs = await self.CRUDAudit.list(query=query, sort=[("created_at", -1)], limit=limit)
            return [self._format(l) for l in logs]
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in AuditLogController.list: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def history_for_record(self, record_id: str, collection_name: str, auth: Dict[str, Any]) -> List[dict]:
        """Return the audit history for a specific record.

        Answers "who changed this number" queries.

        Args:
            record_id: Record id.
            collection_name: Collection name.
            auth: Authenticated user.

        Returns:
            List[dict]: Audit log payloads.
        """
        try:
            logging.info("Executing AuditLogController.history_for_record")
            require_roles(auth["role"], [UserRole.ADMIN.value])
            if not ObjectId.is_valid(record_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="record_id must be a valid ObjectId",
                )
            logs = await self.CRUDAudit.history(record_id=ObjectId(record_id), collection_name=collection_name)
            return [self._format(l) for l in logs]
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in AuditLogController.history_for_record: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    @staticmethod
    def _format(l) -> dict:
        """Format an audit log document for response.

        ``old_value`` and ``new_value`` are recursively normalized so ObjectId and
        datetime values become JSON-serializable strings.

        Args:
            l: Audit log document.

        Returns:
            dict: Response payload.
        """
        return {
            "id": str(l["_id"]),
            "user_id": str(l["user_id"]) if l.get("user_id") else None,
            "user_name": l.get("user_name", ""),
            "action": l.get("action"),
            "collection_name": l.get("collection_name"),
            "record_id": str(l["record_id"]) if l.get("record_id") else None,
            "warehouse_id": str(l["warehouse_id"]) if l.get("warehouse_id") else None,
            "old_value": to_dict(l.get("old_value") or {}),
            "new_value": to_dict(l.get("new_value") or {}),
            "method": l.get("method"),
            "ip_address": l.get("ip_address", ""),
            "created_at": l.get("created_at"),
        }

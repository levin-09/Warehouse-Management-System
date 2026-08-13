"""User controller."""
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import HTTPException, status

from commons.auth import hash_password
from core import logger
from core.cruds.audit_log_crud import CRUDAuditLog
from core.cruds.user_crud import CRUDUser
from core.models.enums import AuditMethod, UserRole
from core.utils.custom.database_helper import utc_timestamp
from core.utils.rbac import check_delete, check_read, require_roles, same_warehouse

logging = logger(__name__)


class UserController:
    """Orchestrates user management with admin-only write rules."""

    def __init__(self) -> None:
        """Initialize user and audit CRUDs."""
        self.CRUDUser = CRUDUser()
        self.CRUDAudit = CRUDAuditLog()

    async def create_user(self, data: Dict[str, Any], auth: Dict[str, Any]) -> Dict[str, Any]:
        """Create a warehouse staff user (admin only).

        Args:
            data: User creation data.
            auth: Authenticated user details.

        Returns:
            dict: Created user payload.

        Raises:
            HTTPException 403: Not admin.
            HTTPException 400: Email already in use.
        """
        try:
            logging.info("Executing UserController.create_user")
            require_roles(auth["role"], [UserRole.ADMIN.value])
            existing = await self.CRUDUser.get_by_email(email=data["email"])
            if existing:
                logging.warning(f"User with email {data['email']} already exists")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
            user = await self.CRUDUser.create(
                obj_in={
                    "full_name": data["full_name"],
                    "email": data["email"],
                    "password_hash": hash_password(data["password"]),
                    "role": data["role"],
                    "warehouse_id": ObjectId(data["warehouse_id"]),
                    "is_active": data.get("is_active", True),
                }
            )
            await self._audit(auth, "user_created", "users", user["_id"], {}, user)
            return self._format(user)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in UserController.create_user: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def list_users(self, auth: Dict[str, Any], role: Optional[str] = None) -> List[dict]:
        """List users visible to the caller.

        Args:
            auth: Authenticated user details.
            role: Optional role filter.

        Returns:
            List[dict]: User payloads.
        """
        try:
            logging.info("Executing UserController.list_users")
            check_read(auth["role"], "users")
            query: Dict[str, Any] = {}
            if role:
                query["role"] = role
            if auth["role"] == UserRole.MANAGER.value:
                query["warehouse_id"] = ObjectId(auth["warehouse_id"]) if auth.get("warehouse_id") else None
                query["role"] = {"$ne": UserRole.ADMIN.value}
            users = await self.CRUDUser.list(query=query)
            return [self._format(u) for u in users]
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in UserController.list_users: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def update_user(self, user_id: str, data: Dict[str, Any], auth: Dict[str, Any]) -> dict:
        """Update a user (admin or manager for their warehouse).

        Args:
            user_id: Target user id.
            data: Update data.
            auth: Authenticated user details.

        Returns:
            dict: Updated user payload.

        Raises:
            HTTPException 404: User not found.
            HTTPException 403: Not permitted.
        """
        try:
            logging.info("Executing UserController.update_user")
            user = await self.CRUDUser.get_by_id(id=user_id)
            if user is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            require_roles(auth["role"], [UserRole.ADMIN.value, UserRole.MANAGER.value])
            if auth["role"] != UserRole.ADMIN.value:
                if not same_warehouse(auth.get("warehouse_id"), user.get("warehouse_id")):
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            payload: Dict[str, Any] = {}
            for field in ("full_name", "role", "is_active"):
                if field in data and data[field] is not None:
                    payload[field] = data[field]
            if data.get("warehouse_id"):
                payload["warehouse_id"] = ObjectId(data["warehouse_id"])
            if not payload:
                return self._format(user)
            old = dict(user)
            updated = await self.CRUDUser.update(id=user_id, update_data=payload)
            await self._audit(auth, "user_updated", "users", user["_id"], old, updated)
            return self._format(updated)
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in UserController.update_user: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def delete_user(self, user_id: str, auth: Dict[str, Any]) -> dict:
        """Delete a user (admin only).

        Args:
            user_id: Target user id.
            auth: Authenticated user details.

        Returns:
            dict: Confirmation message.

        Raises:
            HTTPException 404: User not found.
            HTTPException 403: Not admin.
        """
        try:
            logging.info("Executing UserController.delete_user")
            user = await self.CRUDUser.get_by_id(id=user_id)
            if user is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            require_roles(auth["role"], [UserRole.ADMIN.value])
            check_delete(auth["role"], "users")
            await self.CRUDUser.delete(id=user_id)
            await self._audit(auth, "user_deleted", "users", ObjectId(user_id), user, {})
            return {"message": "User deleted"}
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in UserController.delete_user: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def change_password(self, auth: Dict[str, Any], old_password: str, new_password: str) -> dict:
        """Change the authenticated user's own password.

        Args:
            auth: Authenticated user details.
            old_password: Current password.
            new_password: New password.

        Returns:
            dict: Confirmation message.

        Raises:
            HTTPException 400: Old password incorrect.
        """
        try:
            from commons.auth import verify_password

            logging.info("Executing UserController.change_password")
            user = await self.CRUDUser.get_by_id(id=auth["id"])
            if not verify_password(old_password, user.get("password_hash", "")):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect")
            await self.CRUDUser.update(id=auth["id"], update_data={"password_hash": hash_password(new_password)})
            return {"message": "Password changed"}
        except HTTPException:
            raise
        except Exception as error:
            logging.error(f"Error in UserController.change_password: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

    async def _audit(self, auth, action, coll, record_id, old, new) -> None:
        """Write an audit log entry.

        ``old``/``new`` are scrubbed of secret fields (``password_hash``) before
        storage so sensitive credentials are never persisted to the audit trail.

        Args:
            auth: Authenticated user details.
            action: Action label.
            coll: Collection name.
            record_id: Record id.
            old: Old value.
            new: New value.
        """
        await self.CRUDAudit.create(
            obj_in={
                "user_id": ObjectId(auth["id"]),
                "user_name": auth.get("full_name", ""),
                "action": action,
                "collection_name": coll,
                "record_id": record_id,
                "old_value": self._scrub(old),
                "new_value": self._scrub(new),
                "method": AuditMethod.MANUAL_ENTRY.value,
                "created_at": utc_timestamp(),
            }
        )

    @staticmethod
    def _scrub(value: Dict[str, Any]) -> Dict[str, Any]:
        """Remove secret fields from a value before storing it in an audit log.

        Args:
            value: The value to scrub.

        Returns:
            dict: The scrubbed value with sensitive fields removed.
        """
        if not isinstance(value, dict):
            return value or {}
        return {k: v for k, v in value.items() if k != "password_hash"}

    @staticmethod
    def _format(user) -> dict:
        """Format a user document for response.

        Args:
            user: User document.

        Returns:
            dict: Response payload.
        """
        return {
            "id": str(user["_id"]),
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"],
            "warehouse_id": str(user.get("warehouse_id") or ""),
            "is_active": user.get("is_active", True),
            "last_login": user.get("last_login"),
        }

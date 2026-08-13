"""Base CRUD providing shared persistence operations for domain CRUD classes.

Domain CRUD classes subclass this and keep collection/query specifics local.
"""
from typing import Any, Dict, List, Optional

from bson import ObjectId

from core import logger
from core.database.database import collection
from core.utils.custom.database_helper import str_to_object_id, utc_timestamp

logging = logger(__name__)


class BaseCRUD:
    """Generic async persistence wrapper around a single MongoDB collection."""

    COLLECTION_NAME: str = ""

    def __init__(self) -> None:
        """Initialize the collection handle."""
        self.coll = collection(self.COLLECTION_NAME)

    async def create(self, *, obj_in: dict) -> Optional[Dict[str, Any]]:
        """Insert a document and return it with its generated id.

        Args:
            obj_in: Data to insert.

        Returns:
            Optional[dict]: The created document, or None if insertion failed.
        """
        try:
            logging.info(f"Executing {type(self).__name__}.create")
            data = dict(obj_in)
            data["created_at"] = data.get("created_at", utc_timestamp())
            result = await self.coll.insert_one(data)
            return await self.get_by_id(id=result.inserted_id)
        except Exception as error:
            logging.error(f"Error in {type(self).__name__}.create: {error}")
            raise

    async def get_by_id(self, *, id: Any) -> Optional[Dict[str, Any]]:
        """Fetch a single document by id.

        Args:
            id: Document id (string or ObjectId).

        Returns:
            Optional[dict]: The document, or None if not found.
        """
        try:
            logging.info(f"Executing {type(self).__name__}.get_by_id")
            return await self.coll.find_one({"_id": str_to_object_id(id)})
        except Exception as error:
            logging.error(f"Error in {type(self).__name__}.get_by_id: {error}")
            raise

    async def get_one(self, *, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fetch a single document matching a query.

        Args:
            query: MongoDB query filter.

        Returns:
            Optional[dict]: The document, or None if not found.
        """
        try:
            logging.info(f"Executing {type(self).__name__}.get_one")
            return await self.coll.find_one(query)
        except Exception as error:
            logging.error(f"Error in {type(self).__name__}.get_one: {error}")
            raise

    async def list(
        self, *, query: Dict[str, Any] = None, sort: Optional[list] = None, skip: int = 0, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List documents matching a query with paging.

        Args:
            query: MongoDB query filter.
            sort: Optional sort spec.
            skip: Number of documents to skip.
            limit: Maximum documents to return.

        Returns:
            List[dict]: Matching documents.
        """
        try:
            logging.info(f"Executing {type(self).__name__}.list")
            query = query or {}
            cursor = self.coll.find(query)
            if sort:
                cursor = cursor.sort(sort)
            cursor = cursor.skip(skip).limit(limit)
            return [doc async for doc in cursor]
        except Exception as error:
            logging.error(f"Error in {type(self).__name__}.list: {error}")
            raise

    async def count(self, *, query: Dict[str, Any] = None) -> int:
        """Count documents matching a query.

        Args:
            query: MongoDB query filter.

        Returns:
            int: Count of matching documents.
        """
        try:
            logging.info(f"Executing {type(self).__name__}.count")
            return await self.coll.count_documents(query or {})
        except Exception as error:
            logging.error(f"Error in {type(self).__name__}.count: {error}")
            raise

    async def update(self, *, id: Any, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a single document by id.

        Args:
            id: Document id.
            update_data: Fields to set.

        Returns:
            Optional[dict]: The updated document, or None if not found.
        """
        try:
            logging.info(f"Executing {type(self).__name__}.update")
            await self.coll.update_one({"_id": str_to_object_id(id)}, {"$set": update_data})
            return await self.get_by_id(id=id)
        except Exception as error:
            logging.error(f"Error in {type(self).__name__}.update: {error}")
            raise

    async def delete(self, *, id: Any) -> bool:
        """Delete a single document by id.

        Args:
            id: Document id.

        Returns:
            bool: True if a document was deleted.
        """
        try:
            logging.info(f"Executing {type(self).__name__}.delete")
            result = await self.coll.delete_one({"_id": str_to_object_id(id)})
            return result.deleted_count > 0
        except Exception as error:
            logging.error(f"Error in {type(self).__name__}.delete: {error}")
            raise

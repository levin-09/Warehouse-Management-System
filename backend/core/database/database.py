"""Database lifecycle and shared persistence setup.

Creates and exposes the async MongoDB client/database, provides collection
helpers used by CRUD classes, and tracks connectivity for startup/shutdown.
"""
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from core.config import settings
from core import logger

logging = logger(__name__)

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


def get_client() -> AsyncIOMotorClient:
    """Return the shared async MongoDB client.

    Creates the client on first use if it does not already exist.

    Returns:
        AsyncIOMotorClient: The shared client.

    Raises:
        RuntimeError: If the client is not connected.
    """
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongodb_uri)
    return _client


def get_db() -> AsyncIOMotorDatabase:
    """Return the shared database handle.

    Creates the client if needed and returns the configured database.

    Returns:
        AsyncIOMotorDatabase: The shared database.
    """
    global _db
    if _db is None:
        _db = get_client()[settings.mongodb_db_name]
    return _db


async def ping() -> bool:
    """Check that the database is reachable.

    Returns:
        bool: True if a ping command succeeds.
    """
    try:
        await get_client().admin.command("ping")
        return True
    except Exception as error:
        logging.error(f"Database ping failed: {error}")
        return False


async def close() -> None:
    """Close the shared MongoDB client connection."""
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None
    logging.info("MongoDB client closed")


async def connect() -> None:
    """Establish and verify the database connection."""
    logging.info("Connecting to MongoDB")
    get_db()
    if not await ping():
        logging.warning("MongoDB reachable check failed during connect")


def collection(name: str):
    """Return a collection from the shared database.

    Args:
        name: Collection name.

    Returns:
        AsyncIOMotorCollection: The requested collection.
    """
    return get_db()[name]

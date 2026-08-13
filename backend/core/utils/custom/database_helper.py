"""Database utility helpers shared across CRUD layers."""
from datetime import datetime, timezone
from typing import Any, Dict

from bson import ObjectId


def utc_timestamp() -> str:
    """Return the current UTC time as an ISO-8601 string.

    Returns:
        str: ISO-8601 UTC timestamp.
    """
    return datetime.now(timezone.utc).isoformat()


def to_dict(document: Any) -> Dict[str, Any]:
    """Convert a MongoDB document/dict into a JSON-friendly dict.

    Converts ``ObjectId`` instances to their string representation recursively.

    Args:
        document: A pydantic model, dict, or Mongo document.

    Returns:
        dict: A dict with ``_id`` stringified.
    """
    if document is None:
        return {}
    data = dict(document) if hasattr(document, "model_dump") else dict(document)
    result: Dict[str, Any] = {}
    for key, value in data.items():
        if key == "_id" and isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            result[key] = to_dict(value)
        elif isinstance(value, list):
            result[key] = [
                to_dict(v) if isinstance(v, dict)
                else str(v) if isinstance(v, ObjectId)
                else v.isoformat() if isinstance(v, datetime)
                else v
                for v in value
            ]
        else:
            result[key] = value
    return result


def str_to_object_id(value: Any) -> Any:
    """Convert a string to an ObjectId when possible.

    Args:
        value: The value to convert.

    Returns:
        ObjectId if the value is a valid 24-hex string, otherwise the value unchanged.
    """
    if isinstance(value, str) and ObjectId.is_valid(value):
        return ObjectId(value)
    return value

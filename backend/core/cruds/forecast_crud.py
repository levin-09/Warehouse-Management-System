"""Forecast persistence operations."""
from core.cruds.base_crud import BaseCRUD


class CRUDForecast(BaseCRUD):
    """Database access layer for forecast records."""

    COLLECTION_NAME = "forecasts"

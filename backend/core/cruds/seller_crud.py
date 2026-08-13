"""Seller persistence operations."""
from typing import Any, Dict, Optional

from core.cruds.base_crud import BaseCRUD


class CRUDSeller(BaseCRUD):
    """Database access layer for seller records."""

    COLLECTION_NAME = "sellers"

    async def get_by_email(self, *, email: str) -> Optional[Dict[str, Any]]:
        """Fetch a seller by portal/contact email.

        Args:
            email: Seller email.

        Returns:
            Optional[dict]: The seller document, or None.
        """
        return await self.get_one(query={"email": email})

    async def get_by_company(self, *, company_name: str) -> Optional[Dict[str, Any]]:
        """Fetch a seller by company name.

        Args:
            company_name: Company name.

        Returns:
            Optional[dict]: The seller document, or None.
        """
        return await self.get_one(query={"company_name": company_name})

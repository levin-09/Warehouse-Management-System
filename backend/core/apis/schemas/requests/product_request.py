"""Product request schemas."""
from typing import Optional

from pydantic import BaseModel, Field


class DimensionsCreate(BaseModel):
    """Product physical dimensions."""

    weight_lbs: float = 0.0
    length_in: float = 0.0
    width_in: float = 0.0
    height_in: float = 0.0


class ProductCreate(BaseModel):
    """Payload to create a product."""

    seller_id: str
    upc_barcode: str
    sku: str
    product_name: str
    description: str = ""
    dimensions: DimensionsCreate = Field(default_factory=DimensionsCreate)
    low_stock_threshold: int = 20
    category: str = ""
    is_active: bool = True


class ProductUpdate(BaseModel):
    """Payload to update a product."""

    sku: Optional[str] = None
    product_name: Optional[str] = None
    description: Optional[str] = None
    dimensions: Optional[DimensionsCreate] = None
    low_stock_threshold: Optional[int] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None

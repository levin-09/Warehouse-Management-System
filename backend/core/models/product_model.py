"""Product model — the product catalog."""
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field

COLLECTION = "products"


class Dimensions(BaseModel):
    """Physical dimensions of a product."""

    weight_lbs: float = 0.0
    length_in: float = 0.0
    width_in: float = 0.0
    height_in: float = 0.0


class Product(BaseModel):
    """A product that passes through the warehouses."""

    id: Optional[ObjectId] = Field(default=None, alias="_id")
    seller_id: ObjectId
    upc_barcode: str
    sku: str
    product_name: str
    description: str = ""
    dimensions: Dimensions = Field(default_factory=Dimensions)
    low_stock_threshold: int = 20
    category: str = ""
    is_active: bool = True

    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}

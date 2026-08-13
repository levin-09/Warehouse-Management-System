"""Product response schemas."""
from pydantic import BaseModel


class DimensionsResponse(BaseModel):
    """Product physical dimensions."""

    weight_lbs: float
    length_in: float
    width_in: float
    height_in: float


class ProductResponse(BaseModel):
    """Product representation."""

    id: str
    seller_id: str
    upc_barcode: str
    sku: str
    product_name: str
    description: str
    dimensions: DimensionsResponse
    low_stock_threshold: int
    category: str
    is_active: bool

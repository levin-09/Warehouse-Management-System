"""Product routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from commons.dependencies import get_current_user
from core import logger
from core.apis.schemas.requests.product_request import ProductCreate, ProductUpdate
from core.apis.schemas.responses.product_response import ProductResponse
from core.controllers.product_controller import ProductController

product_router = APIRouter(prefix="/v1/products", tags=["Products"])
logging = logger(__name__)


@product_router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(request: ProductCreate, auth: dict = Depends(get_current_user)):
    """
    Create a product.

    Args:
        request (ProductCreate): Product payload.
        auth (dict): Authenticated user claims.

    Returns:
        ProductResponse: Created product.
    """
    try:
        logging.info("Calling POST /v1/products endpoint")
        response = await ProductController().create(request.model_dump(), auth)
        return ProductResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in POST /v1/products endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in POST /v1/products endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@product_router.get("", response_model=list[ProductResponse])
async def list_products(seller_id: Optional[str] = Query(default=None), auth: dict = Depends(get_current_user)):
    """
    List products.

    Args:
        seller_id (Optional[str]): Seller filter.
        auth (dict): Authenticated user claims.

    Returns:
        list[ProductResponse]: Products.
    """
    try:
        logging.info("Calling GET /v1/products endpoint")
        response = await ProductController().list(auth, seller_id)
        return [ProductResponse(**p) for p in response]
    except HTTPException as error:
        logging.error(f"Error in GET /v1/products endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/products endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@product_router.get("/upc/{upc}", response_model=ProductResponse)
async def get_product_by_upc(upc: str, auth: dict = Depends(get_current_user)):
    """
    Fetch a product by UPC barcode.

    Args:
        upc (str): UPC barcode.
        auth (dict): Authenticated user claims.

    Returns:
        ProductResponse: Product.
    """
    try:
        logging.info(f"Calling GET /v1/products/upc/{upc} endpoint")
        response = await ProductController().get_by_upc(upc, auth)
        return ProductResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in GET /v1/products/upc/{upc} endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/products/upc/{upc} endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@product_router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, auth: dict = Depends(get_current_user)):
    """
    Fetch a product by id.

    Args:
        product_id (str): Product id.
        auth (dict): Authenticated user claims.

    Returns:
        ProductResponse: Product.
    """
    try:
        logging.info(f"Calling GET /v1/products/{product_id} endpoint")
        response = await ProductController().get(product_id, auth)
        return ProductResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in GET /v1/products/{product_id} endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in GET /v1/products/{product_id} endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@product_router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, request: ProductUpdate, auth: dict = Depends(get_current_user)):
    """
    Update a product.

    Args:
        product_id (str): Product id.
        request (ProductUpdate): Update payload.
        auth (dict): Authenticated user claims.

    Returns:
        ProductResponse: Updated product.
    """
    try:
        logging.info(f"Calling PATCH /v1/products/{product_id} endpoint")
        response = await ProductController().update(product_id, request.model_dump(), auth)
        return ProductResponse(**response)
    except HTTPException as error:
        logging.error(f"Error in PATCH /v1/products/{product_id} endpoint: {error}")
        raise error
    except Exception as error:
        logging.error(f"Error in PATCH /v1/products/{product_id} endpoint: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

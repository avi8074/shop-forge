"""
Compatibility layer for schemas.
Exports all schemas from the schemas package.
"""
from schemas.ai import (
    ProductAnalysisResponse,
    ImageBase64Request,
    MediaData,
    CatalogProductWithMedia,
)
from schemas.product import ProductCreate, ProductUpdate
from schemas.user import UserCreate, UserLogin
from schemas.store import StoreCreate, StoreUpdate
from schemas.category import CategoryCreate, CategoryUpdate

__all__ = [
    "ProductAnalysisResponse",
    "ImageBase64Request",
    "MediaData",
    "CatalogProductWithMedia",
    "ProductCreate",
    "ProductUpdate",
    "UserCreate",
    "UserLogin",
    "StoreCreate",
    "StoreUpdate",
    "CategoryCreate",
    "CategoryUpdate",
]

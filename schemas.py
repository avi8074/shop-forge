from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProductAnalysisResponse(BaseModel):
    product_name: str
    category: str
    tags: list[str]
    description: str
    ocr_text: str


class ImageBase64Request(BaseModel):
    image_base64: str


class MediaData(BaseModel):
    model_config = ConfigDict(extra="allow")


class CatalogProductWithMedia(ProductAnalysisResponse):
    media: dict[str, Any]


class UserCreate(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class StoreCreate(BaseModel):
    name: str
    tagline: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    subdomain: Optional[str] = None
    theme: Optional[str] = None
    banner_image: Optional[str] = None
    logo_image: Optional[str] = None


class StoreUpdate(BaseModel):
    name: Optional[str] = None
    tagline: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    subdomain: Optional[str] = None
    theme: Optional[str] = None
    banner_image: Optional[str] = None
    logo_image: Optional[str] = None


class CategoryCreate(BaseModel):
    name: str
    store_id: int


class CategoryUpdate(BaseModel):
    name: Optional[str] = None


class ProductBase(BaseModel):
    sku: Optional[str] = None
    name: str
    description: Optional[str] = None
    price: Optional[str] = None
    mrp: Optional[str] = None
    cogs: Optional[str] = None
    image_url: Optional[str] = None
    cloudinary_public_id: Optional[str] = None
    ai_category: Optional[str] = None
    ai_tags: Optional[str] = None
    sizes: Optional[str] = None
    in_stock: bool = True
    wa_inquiries: int = 0
    wa_converted: int = 0
    qr_tag_id: Optional[str] = None
    category_id: Optional[int] = None


class ProductCreate(ProductBase):
    store_id: int


class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[str] = None
    mrp: Optional[str] = None
    cogs: Optional[str] = None
    image_url: Optional[str] = None
    cloudinary_public_id: Optional[str] = None
    ai_category: Optional[str] = None
    ai_tags: Optional[str] = None
    sizes: Optional[str] = None
    in_stock: Optional[bool] = None
    wa_inquiries: Optional[int] = Field(default=None, ge=0)
    wa_converted: Optional[int] = Field(default=None, ge=0)
    qr_tag_id: Optional[str] = None
    category_id: Optional[int] = None


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

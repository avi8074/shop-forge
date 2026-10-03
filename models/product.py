from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String)
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(String)
    mrp = Column(String)
    cogs = Column(String)
    image_url = Column(String)
    cloudinary_public_id = Column(String)
    ai_category = Column(String)
    ai_tags = Column(String)
    sizes = Column(String)
    in_stock = Column(Boolean, default=True)
    wa_inquiries = Column(Integer, default=0)
    wa_converted = Column(Integer, default=0)
    qr_tag_id = Column(String)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))

    store = relationship("Store", back_populates="products")
    category = relationship("Category", back_populates="products")

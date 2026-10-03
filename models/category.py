from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)

    store = relationship("Store", back_populates="categories")
    products = relationship("Product", back_populates="category")

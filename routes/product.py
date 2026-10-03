from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models.category import Category
from models.product import Product
from models.store import Store
from schemas import ProductCreate, ProductUpdate

router = APIRouter()


@router.get("/products")
def list_products(
    store_id: int | None = None,
    category_id: int | None = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    query = db.query(Product).join(Store, Store.id == Product.store_id).filter(Store.owner_id == user_id)
    if store_id is not None:
        query = query.filter(Product.store_id == store_id)
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    return query.all()


@router.post("/products")
def create_product(payload: ProductCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    store = db.query(Store).filter(Store.id == payload.store_id, Store.owner_id == user_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    if payload.category_id is not None:
        category = db.query(Category).filter(Category.id == payload.category_id, Category.store_id == payload.store_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

    product = Product(**payload.model_dump(exclude_none=True))
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    product = db.query(Product).join(Store, Store.id == Product.store_id).filter(Product.id == product_id, Store.owner_id == user_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/products/{product_id}")
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    product = db.query(Product).join(Store, Store.id == Product.store_id).filter(Product.id == product_id, Store.owner_id == user_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    updates = payload.model_dump(exclude_unset=True)
    if "category_id" in updates and updates["category_id"] is not None:
        category = db.query(Category).filter(Category.id == updates["category_id"], Category.store_id == product.store_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

    for key, value in updates.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    product = db.query(Product).join(Store, Store.id == Product.store_id).filter(Product.id == product_id, Store.owner_id == user_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return {"success": True}

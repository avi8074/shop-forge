from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models.category import Category
from models.store import Store
from schemas import CategoryCreate, CategoryUpdate

router = APIRouter()


@router.get("/categories")
def list_categories(store_id: int | None = None, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    query = db.query(Category).join(Store, Store.id == Category.store_id).filter(Store.owner_id == user_id)
    if store_id is not None:
        query = query.filter(Category.store_id == store_id)
    return query.all()


@router.post("/categories")
def create_category(payload: CategoryCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    store = db.query(Store).filter(Store.id == payload.store_id, Store.owner_id == user_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    category = Category(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/categories/{category_id}")
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    category = db.query(Category).join(Store, Store.id == Category.store_id).filter(Category.id == category_id, Store.owner_id == user_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, key, value)

    db.commit()
    db.refresh(category)
    return category

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models.store import Store
from schemas import StoreCreate, StoreUpdate

router = APIRouter()


@router.get("/stores")
def list_stores(db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    return db.query(Store).filter(Store.owner_id == user_id).all()


@router.post("/stores")
def create_store(payload: StoreCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    store = Store(owner_id=user_id, **payload.model_dump(exclude_none=True))
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


@router.get("/stores/{store_id}")
def get_store(store_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    store = db.query(Store).filter(Store.id == store_id, Store.owner_id == user_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store


@router.put("/stores/{store_id}")
def update_store(store_id: int, payload: StoreUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    store = db.query(Store).filter(Store.id == store_id, Store.owner_id == user_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(store, key, value)

    db.commit()
    db.refresh(store)
    return store

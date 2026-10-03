from routes.user import router as user_router
from routes.store import router as store_router
from routes.category import router as category_router
from routes.product import router as product_router

__all__ = ["user_router", "store_router", "category_router", "product_router"]

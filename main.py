import base64
import io
import os
import re
import random
import logging
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, status, Request, Response, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps
from sqlalchemy.orm import Session

# Database and Models
from database import Base, engine, SessionLocal, get_db
from models.user import User
from models.store import Store
from models.category import Category
from models.product import Product

# ShopForge Routes
from routes.store import router as store_router
from routes.category import router as category_router
from routes.product import router as product_router
from routes.user import router as user_router

# AI and Media Pipeline
import media_client
from schemas import ProductAnalysisResponse, ImageBase64Request, MediaData, CatalogProductWithMedia
import ai_engine
from ai_engine import analyze_product_image
from config import get_tesseract_path, GEMINI_API_KEY, OPENROUTER_API_KEY

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("unified_shopforge_ai")


def init_db_and_seed():
    """Initializes tables and seeds default ShopForge store, categories, and multi-category products."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Default User
        user = db.query(User).first()
        if not user:
            user = User(email="admin@shopforge.in", password_hash="dev_demo_hash")
            db.add(user)
            db.commit()
            db.refresh(user)

        # 2. Default Store
        store = db.query(Store).first()
        if not store:
            store = Store(
                name="ShopForge Store",
                tagline="Universal Smart Commerce • Multi-Category Retail Hub",
                city="Bengaluru, KA",
                phone="+91 98450 12345",
                subdomain="shopforge",
                theme="obsidian",
                owner_id=user.id
            )
            db.add(store)
            db.commit()
            db.refresh(store)
        elif store.name == "Mohan Fashions" or "mohan" in (store.subdomain or ""):
            store.name = "ShopForge Store"
            store.tagline = "Universal Smart Commerce • Multi-Category Retail Hub"
            store.subdomain = "shopforge"
            db.commit()

        # 3. Default Universal Categories
        default_cats = [
            "Beverages & Drinks",
            "Footwear & Sneakers",
            "Beauty & Skincare",
            "Home & Kitchen",
            "Books & Stationery",
            "Apparel & Textiles"
        ]
        for cat_name in default_cats:
            existing = db.query(Category).filter(Category.name == cat_name).first()
            if not existing:
                db.add(Category(name=cat_name, store_id=store.id))
        db.commit()

        # 4. Universal Multi-Category Products
        universal_prods = [
            {
                "sku": "SF-DRK-01",
                "name": "Sparkling Citrus Cold Brew - 330ml Can",
                "ai_category": "Beverages & Drinks",
                "ai_tags": "Beverage, Cold Brew, 330ml Can, Zero Sugar, Citrus Zest",
                "price": "149",
                "mrp": "199",
                "cogs": "65",
                "image_url": "/sample_images/beverage_can.jpg",
                "description": "Artisanal sparkling cold brew infused with natural Sicilian citrus zest. 100% natural, chilled liquid energy.",
                "in_stock": True,
                "wa_inquiries": 36,
                "wa_converted": 24,
                "qr_tag_id": "#0841"
            },
            {
                "sku": "SF-FTW-02",
                "name": "AeroPulse Urban Street Sneakers",
                "ai_category": "Footwear & Sneakers",
                "ai_tags": "Footwear, EVA Cushion, Breathable Mesh, Streetwear, UK 7-11",
                "price": "3499",
                "mrp": "4999",
                "cogs": "1650",
                "image_url": "/sample_images/sneakers.png",
                "description": "Engineered dual-density athletic sole with shock-absorption rubber tread and breathable knit upper.",
                "in_stock": True,
                "wa_inquiries": 42,
                "wa_converted": 28,
                "qr_tag_id": "#0842"
            },
            {
                "sku": "SF-SKN-03",
                "name": "HydraGlow Peptide Moisturizer Cream - 50g",
                "ai_category": "Beauty & Skincare",
                "ai_tags": "Skincare, 50g Jar, Hyaluronic Acid, Dermatologist Tested",
                "price": "899",
                "mrp": "1299",
                "cogs": "380",
                "image_url": "/sample_images/skincare_cream.png",
                "description": "Ultra-hydrating peptide cream formulated with organic botanical extracts and multi-molecular hyaluronic acid.",
                "in_stock": True,
                "wa_inquiries": 27,
                "wa_converted": 19,
                "qr_tag_id": "#0843"
            },
            {
                "sku": "SF-HMK-04",
                "name": "Nordic Matte Ceramic Coffee Mug - 350ml",
                "ai_category": "Home & Kitchen",
                "ai_tags": "Ceramics, 350ml Capacity, Microwave Safe, Ergonomic Handle",
                "price": "449",
                "mrp": "699",
                "cogs": "180",
                "image_url": "/sample_images/plain_mug_no_text.png",
                "description": "Handcrafted stoneware mug finished in matte glaze. Dishwasher and microwave safe.",
                "in_stock": True,
                "wa_inquiries": 18,
                "wa_converted": 12,
                "qr_tag_id": "#0844"
            },
            {
                "sku": "SF-BOK-05",
                "name": "The Modern Entrepreneur - Hardcover 1st Edition",
                "ai_category": "Books & Stationery",
                "ai_tags": "Hardcover, 340 Pages, Non-Fiction, Business Strategy",
                "price": "699",
                "mrp": "899",
                "cogs": "290",
                "image_url": "/sample_images/book_cover.jpg",
                "description": "Authoritative handbook on modern business scaling and digital commerce systems. Gold embossed dust jacket.",
                "in_stock": True,
                "wa_inquiries": 22,
                "wa_converted": 15,
                "qr_tag_id": "#0845"
            },
            {
                "sku": "SF-APP-06",
                "name": "Handcrafted Khadi Kurta - Indigo Blue",
                "ai_category": "Apparel & Textiles",
                "ai_tags": "Pure Khadi, Mandarin Collar, Festive, Handspun",
                "price": "1299",
                "mrp": "1999",
                "cogs": "675",
                "image_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuDQBajAH4PfGXNNtPTn1MGWgeABpu-LG4gHnFiJ-qlEfqLdUewsvKYmfbaiDq__0XHXo9Hah19Bzq0SHLIp2SRxWeh6QQCHk7ls9qNhHicJzUdAN8idfjfqGDITCBoPxuhtznTCJRsKmmUN2oTlUUQAH2aDbLPA0Y_-eU2A3z4CeYGmwFB5CBLBo2lpDW3W_nauIfkKrTxAaK9-XrZrrFAvTmJQeBkHwt428lXpBHJR18k_CioisM9p",
                "description": "Woven from handspun Indian khadi with wooden buttons and tailored mandarin collar. Ideal for festive days.",
                "in_stock": True,
                "wa_inquiries": 14,
                "wa_converted": 8,
                "qr_tag_id": "#0846"
            }
        ]

        # Ensure universal products exist
        for prod_info in universal_prods:
            existing = db.query(Product).filter(Product.sku == prod_info["sku"]).first()
            if not existing:
                db.add(Product(store_id=store.id, **prod_info))
        db.commit()
        logger.info("Successfully seeded default products into SQLite catalog.")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: run database migrations and pre-seeding
    init_db_and_seed()
    yield
    # Shutdown


app = FastAPI(
    title="ShopForge & AI Product Intelligence Platform",
    description="Unified platform combining ShopForge e-commerce, Google Gemini Vision, OCR text extraction, and Cloudinary media pipeline.",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for seamless frontend, mobile, and API clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount ShopForge Routers with both /api prefix and root paths
app.include_router(product_router, prefix="/api", tags=["ShopForge Products"])
app.include_router(product_router, tags=["ShopForge Products"])

app.include_router(store_router, prefix="/api", tags=["ShopForge Stores"])
app.include_router(store_router, tags=["ShopForge Stores"])

app.include_router(category_router, prefix="/api", tags=["ShopForge Categories"])
app.include_router(category_router, tags=["ShopForge Categories"])

app.include_router(user_router, prefix="/api", tags=["ShopForge Users"])
app.include_router(user_router, tags=["ShopForge Users"])

# Mount static asset folders
uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

if os.path.exists("sample_images"):
    app.mount("/sample_images", StaticFiles(directory="sample_images"), name="sample_images")

dist_assets_dir = os.path.join(os.path.dirname(__file__), "dist", "assets")
if os.path.exists(dist_assets_dir):
    app.mount("/assets", StaticFiles(directory=dist_assets_dir), name="assets")


# ==============================================================================
# Unified Single Web UI Delivery
# ==============================================================================

@app.get("/", summary="Unified Single Web Interface", response_class=FileResponse)
@app.get("/demo", summary="Unified Single Web Interface", response_class=FileResponse)
@app.get("/ui", summary="Unified Single Web Interface", response_class=FileResponse)
def serve_unified_web():
    """Serves the modern unified VisualDraft React single-page application."""
    dist_index = os.path.join(os.path.dirname(__file__), "dist", "index.html")
    if os.path.exists(dist_index):
        return FileResponse(dist_index)
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return JSONResponse({
        "status": "online",
        "service": "ShopForge & AI Product Intelligence Platform",
        "instructions": "Run 'npm run build' in visualdraft (2) to compile the modern frontend."
    })


# ==============================================================================
# Health and AI Configuration
# ==============================================================================

@app.get("/health", summary="Health Check Endpoint")
def health_check():
    import config
    tesseract_path = get_tesseract_path()
    has_gemini = bool(config.GEMINI_API_KEY)
    has_openrouter = bool(config.OPENROUTER_API_KEY and not config.OPENROUTER_API_KEY.startswith("export"))
    active_engine = "Gemini 2.5 Flash Vision" if has_gemini else ("OpenRouter Vision" if has_openrouter else "Computer Vision & Spatial Geometry Engine")
    media_health = media_client.check_media_health()

    return {
        "status": "healthy",
        "service": "ShopForge & AI Product Intelligence Platform",
        "version": "2.0.0",
        "ocr_engine": {
            "tesseract_available": bool(tesseract_path),
            "tesseract_path": tesseract_path or "Not found (using fallback)"
        },
        "ai_engine": {
            "gemini_api_configured": has_gemini,
            "openrouter_configured": has_openrouter,
            "active_engine": active_engine,
            "heuristic_fallback_active": not (has_gemini or has_openrouter)
        },
        "media_pipeline": media_health,
        "database": {
            "engine": "SQLite",
            "file": "shopforge.db",
            "status": "connected"
        }
    }


@app.post("/config/api-key", summary="Configure Gemini or OpenRouter API Key")
async def update_api_key(request: Request):
    try:
        body = await request.json()
        gemini_key = body.get("gemini_api_key", "").strip()
        openrouter_key = body.get("openrouter_api_key", "").strip()

        import config
        import ai_engine

        if gemini_key:
            try:
                from google import genai
                client = genai.Client(api_key=gemini_key)
                test_resp = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents="Reply with 'OK'"
                )
                if not test_resp.text:
                    raise ValueError("Empty response received from Gemini API.")
            except Exception as test_err:
                raise HTTPException(
                    status_code=400,
                    detail=f"Gemini API Key validation failed: {str(test_err)}"
                )

            config.GEMINI_API_KEY = gemini_key
            ai_engine.GEMINI_API_KEY = gemini_key

            # Persist to .env
            env_path = os.path.join(os.path.dirname(__file__), ".env")
            env_content = ""
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    env_content = f.read()

            if "GEMINI_API_KEY=" in env_content:
                env_content = re.sub(r'GEMINI_API_KEY=.*', f'GEMINI_API_KEY={gemini_key}', env_content)
            else:
                env_content += f"\nGEMINI_API_KEY={gemini_key}\n"

            with open(env_path, "w", encoding="utf-8") as f:
                f.write(env_content)

            return {
                "success": True,
                "engine": "Gemini 2.5 Flash Vision",
                "message": "Google Gemini 2.5 Flash Multimodal Vision successfully verified and activated!"
            }

        if openrouter_key:
            config.OPENROUTER_API_KEY = openrouter_key
            ai_engine.OPENROUTER_API_KEY = openrouter_key
            return {
                "success": True,
                "engine": "OpenRouter Vision",
                "message": "OpenRouter Vision API key configured!"
            }

        raise HTTPException(status_code=400, detail="No API key provided.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring API key: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to configure API key: {str(e)}")


# ==============================================================================
# Image Helpers
# ==============================================================================

def parse_image_bytes(image_bytes: bytes) -> Image.Image:
    try:
        pil_image = Image.open(io.BytesIO(image_bytes))
        pil_image.load()
        try:
            pil_image = ImageOps.exif_transpose(pil_image)
        except Exception:
            pass
        return pil_image
    except Exception as e:
        logger.error(f"Invalid image format: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image file format or corrupt image data. Error: {str(e)}"
        )


def decode_base64_image(base64_str: str) -> Image.Image:
    if not base64_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="image_base64 string cannot be empty."
        )

    if "," in base64_str:
        base64_str = base64_str.split(",", 1)[1]

    try:
        img_bytes = base64.b64decode(base64_str)
        return parse_image_bytes(img_bytes)
    except Exception as e:
        logger.error(f"Failed to decode base64 image: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to decode image_base64 string. Error: {str(e)}"
        )


# ==============================================================================
# AI Analysis Endpoints
# ==============================================================================

@app.post(
    "/analyze-product",
    response_model=ProductAnalysisResponse,
    summary="Analyze Product Image",
    description="Accepts a product image via multipart form-data (field 'image') OR JSON body ({'image_base64': '...'}) and returns exact JSON product intelligence."
)
@app.post("/api/ai/analyze", response_model=ProductAnalysisResponse)
async def analyze_product(
    request: Request,
    response: Response,
    image: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None)
):
    pil_image = None

    if image is not None:
        contents = await image.read()
        if contents:
            pil_image = parse_image_bytes(contents)
    elif image_base64 is not None:
        pil_image = decode_base64_image(image_base64)

    if pil_image is None:
        try:
            content_type = request.headers.get("content-type", "").lower()
            if "application/json" in content_type:
                body = await request.json()
                b64_str = body.get("image_base64") or body.get("image") or body.get("imageBase64") or ""
                if b64_str:
                    pil_image = decode_base64_image(b64_str)
            elif "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
                form = await request.form()
                for key in ["image", "file", "photo", "upload", "product", "image_file"]:
                    item = form.get(key)
                    if hasattr(item, "read"):
                        data = await item.read()
                        if data:
                            pil_image = parse_image_bytes(data)
                            break
                if pil_image is None and "image_base64" in form:
                    pil_image = decode_base64_image(str(form["image_base64"]))
        except Exception as e:
            logger.debug(f"Request body parsing attempt: {e}")

    if pil_image is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No product image provided. Please upload an image file using multipart field 'image' or send a JSON body with 'image_base64'."
        )

    try:
        result = analyze_product_image(pil_image)
        engine_used = getattr(ai_engine, "LAST_ENGINE_USED", "computer_vision")
        response.headers["X-AI-Engine"] = engine_used
        return ProductAnalysisResponse(**result)
    except Exception as e:
        logger.error(f"Error during product image analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while analyzing the product image: {str(e)}"
        )


# ==============================================================================
# Media Pipeline Endpoints
# ==============================================================================

@app.get("/api/media/health", summary="Check Cloudinary Media Pipeline Health")
def get_media_health():
    return media_client.check_media_health()


@app.post("/api/media/upload", summary="Upload Single Image")
async def upload_single_media(
    image: UploadFile = File(...),
    shopId: Optional[str] = Form("default-shop"),
    productId: Optional[str] = Form(""),
    name: Optional[str] = Form(""),
    category: Optional[str] = Form(""),
    removeBackground: Optional[str] = Form("true")
):
    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    is_remove_bg = removeBackground.lower() not in ["false", "0", "no", "off"] if removeBackground else True
    data = media_client.upload_media(
        image_bytes=contents,
        filename=image.filename or "upload.jpg",
        content_type=image.content_type or "image/jpeg",
        shop_id=shopId or "default-shop",
        product_id=productId or "",
        name=name or "",
        category=category or "",
        remove_background=is_remove_bg
    )
    return {"success": True, "data": data}


@app.post("/api/media/upload-bulk", summary="Bulk Upload Images")
async def upload_bulk_media(
    images: List[UploadFile] = File(...),
    shopId: Optional[str] = Form("default-shop"),
    category: Optional[str] = Form(""),
    removeBackground: Optional[str] = Form("true")
):
    if not images or len(images) == 0:
        raise HTTPException(status_code=400, detail="No files uploaded.")
    if len(images) > 20:
        raise HTTPException(status_code=400, detail="Too many files. Maximum allowed is 20 per request.")

    files_data = []
    for f in images:
        b = await f.read()
        files_data.append((f.filename or "product.jpg", b, f.content_type or "image/jpeg"))

    is_remove_bg = removeBackground.lower() not in ["false", "0", "no", "off"] if removeBackground else True
    return media_client.upload_media_bulk(
        files_data=files_data,
        shop_id=shopId or "default-shop",
        category=category or "",
        remove_background=is_remove_bg
    )


@app.delete("/api/media", summary="Delete Asset")
def delete_media_asset(
    publicId: Optional[str] = None,
    public_id: Optional[str] = None
):
    target_id = publicId or public_id
    if not target_id:
        raise HTTPException(status_code=400, detail="publicId query parameter is required.")

    data = media_client.delete_media(target_id)
    return {"success": True, "data": data}


# ==============================================================================
# End-to-End AI Analysis + Media Ingestion
# ==============================================================================

@app.post(
    "/analyze-and-process-product",
    response_model=CatalogProductWithMedia,
    summary="End-to-End AI Analysis & Media Ingestion",
    description="Analyzes the product image with AI vision, generates naming/tags/category, and automatically creates responsive 1000px, card, and thumbnail variants."
)
@app.post("/api/products/ingest-from-image", response_model=CatalogProductWithMedia)
async def analyze_and_process_product(
    request: Request,
    response: Response,
    image: Optional[UploadFile] = File(None),
    shopId: Optional[str] = Form("default-shop"),
    productId: Optional[str] = Form(""),
    removeBackground: Optional[str] = Form("true")
):
    contents = None
    filename = "product.jpg"
    content_type = "image/jpeg"

    if image is not None:
        contents = await image.read()
        filename = image.filename or filename
        content_type = image.content_type or content_type

    if not contents:
        try:
            form = await request.form()
            for key in ["image", "file", "photo", "upload"]:
                item = form.get(key)
                if hasattr(item, "read"):
                    contents = await item.read()
                    filename = getattr(item, "filename", filename)
                    content_type = getattr(item, "content_type", content_type)
                    break
        except Exception:
            pass

    if not contents:
        raise HTTPException(status_code=400, detail="Please upload a product image under field 'image'.")

    pil_image = parse_image_bytes(contents)

    # 1. Run AI Product Analysis
    result = analyze_product_image(pil_image)
    engine_used = getattr(ai_engine, "LAST_ENGINE_USED", "computer_vision")
    response.headers["X-AI-Engine"] = engine_used

    # 2. Ingest into Media Pipeline
    is_remove_bg = removeBackground.lower() not in ["false", "0", "no", "off"] if removeBackground else True
    media_data = media_client.upload_media(
        image_bytes=contents,
        filename=filename,
        content_type=content_type,
        shop_id=shopId or "default-shop",
        product_id=productId or "",
        name=result.get("product_name", ""),
        category=result.get("category", ""),
        remove_background=is_remove_bg
    )

    return CatalogProductWithMedia(
        product_name=result["product_name"],
        category=result["category"],
        tags=result["tags"],
        description=result["description"],
        ocr_text=result["ocr_text"],
        media=media_data
    )


# ==============================================================================
# SPA Fallback Route
# ==============================================================================

@app.get("/{full_path:path}", include_in_schema=False)
def catch_all(full_path: str):
    """Fallback handler for React SPA client-side routing."""
    # Never intercept backend API endpoints or static mounts
    if full_path.startswith(("api", "docs", "redoc", "openapi.json", "uploads", "sample_images", "assets")):
        raise HTTPException(status_code=404, detail="Endpoint not found")

    dist_index = os.path.join(os.path.dirname(__file__), "dist", "index.html")
    if os.path.exists(dist_index):
        return FileResponse(dist_index)
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    raise HTTPException(status_code=404, detail="Page not found")

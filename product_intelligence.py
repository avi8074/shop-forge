"""
Product Intelligence AI - Standalone Drop-in Module
===================================================
This file consolidates the entire Product Intelligence AI engine, Background Object Cropping Contour Engine,
Brand Recognition, Tesseract OCR text extraction, and FastAPI router into a single module.
"""

import base64
import io
import json
import logging
import os
import re
import shutil
from typing import List, Optional, Dict, Any, Tuple

from fastapi import APIRouter, File, UploadFile, HTTPException, Form, status, Request
from pydantic import BaseModel, Field
from PIL import Image, ImageEnhance, ImageStat
import pytesseract
import numpy as np
import cv2
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("product_intelligence")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""

POSSIBLE_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    os.path.expandvars(r"%LOCALAPPDATA%\Tesseract-OCR\tesseract.exe"),
    shutil.which("tesseract") or ""
]

def get_tesseract_path() -> str:
    for path in POSSIBLE_TESSERACT_PATHS:
        if path and os.path.isfile(path):
            return path
    return ""

tesseract_cmd = get_tesseract_path()
if tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

class ProductAnalysisResponse(BaseModel):
    product_name: str = Field(..., description="Suggested name of the product")
    category: str = Field(..., description="Suggested product category")
    tags: List[str] = Field(default_factory=list, description="Relevant tags as an array")
    description: str = Field(..., description="Short product description")
    ocr_text: str = Field(..., description="Extracted OCR text or empty string")

class ImageBase64Request(BaseModel):
    image_base64: str = Field(..., description="Base64 image string")

GLOBAL_BRANDS = {
    "nike": "Nike", "adidas": "Adidas", "puma": "Puma", "reebok": "Reebok", "jordan": "Air Jordan",
    "new balance": "New Balance", "under armour": "Under Armour", "levis": "Levi's", "zara": "Zara",
    "apple": "Apple", "iphone": "Apple iPhone", "ipad": "Apple iPad", "macbook": "Apple MacBook",
    "samsung": "Samsung", "galaxy": "Samsung Galaxy", "sony": "Sony", "bose": "Bose",
    "coca-cola": "Coca-Cola", "coca cola": "Coca-Cola", "coke": "Coca-Cola", "pepsi": "Pepsi",
    "starbucks": "Starbucks", "nescafe": "Nescafé", "red bull": "Red Bull", "monster": "Monster Energy",
    "nivea": "Nivea", "loreal": "L'Oréal", "dove": "Dove", "colgate": "Colgate",
    "rolex": "Rolex", "omega": "Omega", "ray-ban": "Ray-Ban", "ikea": "IKEA"
}

CATEGORY_KEYWORDS = {
    "Footwear & Sneakers": ["shoe", "shoes", "sneaker", "sneakers", "boot", "boots", "running", "nike", "adidas", "puma", "jordan", "athletic", "sole", "footwear", "leather", "size", "air", "max"],
    "Beverages & Hydration": ["coffee", "tea", "drink", "soda", "water", "juice", "beverage", "cola", "espresso", "latte", "milk", "energy", "caffeine", "can", "bottle", "250ml", "500ml", "750ml", "1l"],
    "Personal Care & Beauty": ["shampoo", "soap", "cream", "lotion", "serum", "facial", "skin", "care", "moisturizer", "cleanser", "spf", "sunscreen", "perfume", "lipstick", "toothpaste", "50ml", "100ml"],
    "Electronics & Gadgets": ["phone", "smartphone", "laptop", "headphone", "headphones", "earbuds", "speaker", "bluetooth", "wireless", "charger", "usb", "watch", "camera", "hd", "led", "ai"],
    "Food & Groceries": ["snack", "chocolate", "cereal", "chips", "organic", "cookie", "cookies", "biscuit", "pasta", "sauce", "protein", "calories", "nutrition", "bar", "crunchy"],
    "Home & Kitchen": ["mug", "cup", "blender", "pan", "pot", "candle", "knife", "container", "cookware", "kitchen", "towel", "storage", "pillow", "vacuum", "dish", "plate"],
    "Books & Stationery": ["book", "handbook", "guide", "python", "novel", "notebook", "journal", "pen", "edition", "author"]
}

def detect_brand(text: str) -> Optional[Tuple[str, str]]:
    if not text:
        return None
    lower = text.lower()
    for kw, title in GLOBAL_BRANDS.items():
        if re.search(r'\b' + re.escape(kw) + r'\b', lower):
            return (kw, title)
    return None

def extract_object_bounding_box(pil_image: Image.Image) -> Dict[str, Any]:
    img_rgb = pil_image.convert("RGB")
    img_np = np.array(img_rgb)
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

    _, binary = cv2.threshold(gray, 225, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        if area > (img_np.shape[0] * img_np.shape[1] * 0.05):
            x, y, w, h = cv2.boundingRect(largest_contour)
            cropped_np = img_np[y:y+h, x:x+w]
            obj_aspect_ratio = w / float(h)
            
            r_avg = np.mean(cropped_np[:, :, 0])
            g_avg = np.mean(cropped_np[:, :, 1])
            b_avg = np.mean(cropped_np[:, :, 2])
            
            edges = cv2.Canny(cv2.cvtColor(cropped_np, cv2.COLOR_RGB2GRAY), 50, 150)
            edge_density = float(np.mean(edges > 0))

            color_desc = "Neutral"
            if r_avg > g_avg + 20 and r_avg > b_avg + 20:
                color_desc = "Red"
            elif b_avg > r_avg + 20 and b_avg > g_avg + 20:
                color_desc = "Blue"
            elif g_avg > r_avg + 20 and g_avg > b_avg + 20:
                color_desc = "Green"
            elif (r_avg + g_avg + b_avg) / 3.0 < 80:
                color_desc = "Dark / Black"

            return {
                "has_object": True,
                "obj_aspect_ratio": obj_aspect_ratio,
                "edge_density": edge_density,
                "color_desc": color_desc
            }

    w, h = img_rgb.size
    return {"has_object": False, "obj_aspect_ratio": w / float(h), "edge_density": 0.05, "color_desc": "Neutral"}

def predict_category_from_object_geometry(vf: Dict[str, Any]) -> Tuple[str, str, List[str]]:
    aspect = vf["obj_aspect_ratio"]
    edges = vf["edge_density"]
    color = vf["color_desc"]

    if aspect >= 1.25:
        if edges > 0.05:
            return ("Footwear & Sneakers", f"Athletic {color} Running Sneaker", ["nike", "shoes", "sneakers", "footwear", "running", "athletic"])
        else:
            return ("Electronics & Gadgets", f"Smart {color} Electronic Device", ["electronics", "gadget", "technology", "smart device"])
    elif aspect <= 0.8:
        if edges > 0.06:
            return ("Books & Stationery", f"Illustrated {color} Reference Book", ["book", "publication", "reading", "stationery"])
        else:
            return ("Beverages & Hydration", f"Hydration {color} Beverage Bottle", ["beverage", "water bottle", "hydration", "drink"])
    else:
        if color in ["Red", "Blue", "Green"]:
            return ("Personal Care & Beauty", f"Nourishing {color} Skincare Product", ["personal care", "skincare", "beauty", "wellness"])
        else:
            return ("Home & Kitchen", f"Essential {color} Ceramic Mug", ["mug", "cup", "kitchenware", "home"])

def preprocess_image_for_ocr(pil_image: Image.Image) -> List[Image.Image]:
    images_to_try = [pil_image]
    try:
        img_np = np.array(pil_image.convert("RGB"))
        gray = cv2.cvtColor(cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR), cv2.COLOR_BGR2GRAY)
        images_to_try.append(Image.fromarray(gray))
    except Exception:
        pass
    return images_to_try

def clean_ocr_text(raw_text: str) -> str:
    if not raw_text:
        return ""
    text = re.sub(r'[\r\n]+', ' ', raw_text)
    text = re.sub(r'[^\x20-\x7E]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    words = [w for w in text.split() if len(w) > 1 or w.isalnum()]
    cleaned = " ".join(words)
    return cleaned if len(cleaned) >= 2 else ""

def extract_ocr_text(pil_image: Image.Image) -> str:
    cmd = getattr(pytesseract.pytesseract, "tesseract_cmd", None) or get_tesseract_path()
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd
        for img in preprocess_image_for_ocr(pil_image):
            try:
                text = pytesseract.image_to_string(img, config="--psm 3")
                cleaned = clean_ocr_text(text)
                if cleaned:
                    return cleaned
            except Exception:
                break
    return ""

def analyze_product_image(pil_image: Image.Image) -> Dict[str, Any]:
    ocr_text = extract_ocr_text(pil_image)
    vf = extract_object_bounding_box(pil_image)
    ocr_lower = ocr_text.lower()
    words = [w for w in ocr_text.split() if len(w) > 1 and not w.isdigit()]

    cat_scores = {}
    for cat_name, kw_list in CATEGORY_KEYWORDS.items():
        score = sum(2 for kw in kw_list if kw in ocr_lower)
        cat_scores[cat_name] = score

    best_cat, top_score = max(cat_scores.items(), key=lambda item: item[1])

    if top_score > 0:
        category = best_cat
        product_name = " ".join(words[:5]).title() if words else f"Premium {category.split('&')[0].strip()} Product"
        tags = [w.lower() for w in words[:6] if len(w) > 2] or ["product", "retail"]
    else:
        category, product_name, tags = predict_category_from_object_geometry(vf)

    brand_match = detect_brand(ocr_text)
    if brand_match:
        brand_kw, brand_title = brand_match
        if brand_title not in product_name:
            product_name = f"{brand_title} {product_name}"
        if brand_kw not in tags:
            tags.insert(0, brand_kw)

    desc = f"High quality {category.lower()} product featuring {vf['color_desc'].lower()} design and durable construction."
    if ocr_text:
        desc += f" Labeled details: '{ocr_text[:80]}'."

    return {
        "product_name": product_name,
        "category": category,
        "tags": tags[:6],
        "description": desc,
        "ocr_text": ocr_text
    }

router = APIRouter()

def parse_image_bytes(image_bytes: bytes) -> Image.Image:
    try:
        pil_image = Image.open(io.BytesIO(image_bytes))
        pil_image.verify()
        return Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")

def decode_base64_image(base64_str: str) -> Image.Image:
    if "," in base64_str:
        base64_str = base64_str.split(",", 1)[1]
    try:
        return parse_image_bytes(base64.b64decode(base64_str))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 string: {str(e)}")

@router.post("/analyze-product", response_model=ProductAnalysisResponse)
async def analyze_product_endpoint(
    request: Request,
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
        raise HTTPException(status_code=400, detail="No product image provided.")

    result = analyze_product_image(pil_image)
    return ProductAnalysisResponse(**result)

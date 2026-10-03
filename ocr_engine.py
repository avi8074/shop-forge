import logging
import re
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pytesseract
import numpy as np
import cv2
from config import get_tesseract_path

logger = logging.getLogger(__name__)

tesseract_cmd = get_tesseract_path()
if tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    logger.info(f"Tesseract OCR path configured: {tesseract_cmd}")


def preprocess_image_for_ocr(pil_image: Image.Image) -> list[Image.Image]:
    """
    Generates high-contrast preprocessed variations of the input image
    to maximize text extraction accuracy from packaging labels.
    """
    images_to_try = [pil_image]
    
    try:
        w, h = pil_image.size
        if w < 800 or h < 800:
            scale = max(800 / w, 800 / h)
            scaled = pil_image.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
            images_to_try.append(scaled)
        else:
            scaled = pil_image

        gray = scaled.convert("L")
        enhancer = ImageEnhance.Contrast(gray)
        high_contrast = enhancer.enhance(2.5)
        images_to_try.append(high_contrast)

        inverted = ImageOps.invert(high_contrast)
        images_to_try.append(inverted)

        img_np = np.array(gray)
        _, thresh = cv2.threshold(img_np, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        images_to_try.append(Image.fromarray(thresh))
    except Exception as e:
        logger.debug(f"Image preprocessing exception: {e}")

    return images_to_try


def clean_ocr_text(raw_text: str) -> str:
    """
    Cleans raw OCR text output while preserving numbers, units, brands, and product details.
    """
    if not raw_text:
        return ""
    
    text = re.sub(r'[\r\n]+', ' ', raw_text)
    text = re.sub(r'[^\x20-\x7E]', ' ', text)
    text = re.sub(r'[^\w\s.,!&%\'\-\/\(\)]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    words = [w for w in text.split() if len(w) > 1 or w.isalnum()]
    cleaned = " ".join(words)
    
    return cleaned if len(cleaned) >= 2 else ""


def extract_ocr_text(pil_image: Image.Image) -> str:
    """
    Extracts readable OCR text using PyTesseract with pre-processing.
    Returns the most complete extracted text string.
    """
    extracted_candidates = []

    current_cmd = getattr(pytesseract.pytesseract, "tesseract_cmd", None) or get_tesseract_path()
    if current_cmd:
        pytesseract.pytesseract.tesseract_cmd = current_cmd
        for img in preprocess_image_for_ocr(pil_image):
            try:
                text = pytesseract.image_to_string(img, config="--psm 3")
                cleaned = clean_ocr_text(text)
                if cleaned:
                    extracted_candidates.append(cleaned)
            except Exception as e:
                logger.debug(f"PyTesseract scan skipped: {e}")
                break

    if not extracted_candidates:
        return ""

    extracted_candidates.sort(key=lambda t: len(t), reverse=True)
    return extracted_candidates[0]

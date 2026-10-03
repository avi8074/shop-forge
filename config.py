import os
import shutil
from dotenv import load_dotenv

load_dotenv()

# Also check for media-pipeline/.env configuration
media_env_path = os.path.join(os.path.dirname(__file__), "media-pipeline", ".env")
if os.path.exists(media_env_path):
    load_dotenv(media_env_path)

# API Keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")

# Cloudinary & Media Pipeline Microservice
MEDIA_PIPELINE_URL = os.getenv("MEDIA_PIPELINE_URL", "http://localhost:5001").rstrip("/")
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

# Default OpenRouter Vision Model
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "qwen/qwen2.5-vl-72b-instruct:free")

# Tesseract executable path search
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

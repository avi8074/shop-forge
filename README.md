# Product Intelligence AI Module

An AI-powered Product Intelligence microservice built with **FastAPI**. It performs image recognition, generates product names, suggests categories, creates relevant tags, writes product descriptions, and extracts OCR text from product images.

Designed specifically for seamless integration into backend services.

---

## 🚀 Features

- **Product Recognition & Attribute Generation**: Generates `product_name`, `category`, `tags`, `description`, and `ocr_text`.
- **Strict Output Schema**: Always returns a consistent, predictable JSON response.
- **Multi-Modal AI Pipeline**:
  - **Primary**: Google Gemini 2.5 Flash Multimodal Vision API (when `GEMINI_API_KEY` is provided).
  - **OCR Engine**: Tesseract OCR (`pytesseract`) with intelligent image preprocessing and EasyOCR fallback.
  - **Offline Computer Vision & NLP Fallback Engine**: Rule-based taxonomy classification, aspect ratio analysis, color metrics, and NLP keyword scoring if operating offline.
- **Flexible Input Methods**:
  - `multipart/form-data` with image file under key `image`
  - `application/json` with base64 encoded image string under key `image_base64`
- **Production-Ready**: Includes health check endpoint (`/health`), CORS enabled (`*`), Pydantic model validation, and automated test suite.

---

## 📋 API Contract

### **Endpoint**: `POST /analyze-product`

#### **Request Formats**

##### **Option A: Multipart Form Data** (`multipart/form-data`)
- **Field Name**: `image` (binary file: PNG, JPEG, WEBP, BMP)

```bash
curl -X POST "http://localhost:8000/analyze-product" \
  -F "image=@/path/to/product_image.jpg"
```

##### **Option B: JSON Payload** (`application/json`)
- **Body Parameter**: `image_base64` (string: base64 encoded image, with or without `data:image/...;base64,` header)

```json
{
  "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQ..."
}
```

```bash
curl -X POST "http://localhost:8000/analyze-product" \
  -H "Content-Type: application/json" \
  -d '{"image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."}'
```

---

### **Exact JSON Output Format**

The endpoint **always** returns the following exact JSON structure without outer markdown wrapping or extra fields:

```json
{
  "product_name": "Suggested Product Name",
  "category": "Suggested Category",
  "tags": [
    "tag1",
    "tag2",
    "tag3",
    "tag4"
  ],
  "description": "Short, clear product description summarizing features.",
  "ocr_text": "Extracted text visible on product label or packaging (empty string if none)"
}
```

#### **Field Specifications**

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `product_name` | `string` | Suggested descriptive name for the product. |
| `category` | `string` | Suggested category (e.g. `Beverages & Hydration`, `Footwear & Sneakers`, `Electronics & Gadgets`, `Personal Care & Beauty`, `Food & Groceries`, `Home & Kitchen`, `Books & Stationery`). |
| `tags` | `array of strings` | List of relevant tags for search & filtering. |
| `description` | `string` | A concise 1-2 sentence product description. |
| `ocr_text` | `string` | Any readable text extracted from product label/packaging using OCR (empty string `""` if none found). |

---

## 🛠️ Additional Endpoints

- `GET /`: Service metadata and sitemap.
- `GET /health`: Health status check, OCR engine availability, and AI configuration state.

---

## 💻 Backend Integration Examples

### **Node.js / Express Integration**

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

async function analyzeProduct(imagePath) {
  const form = new FormData();
  form.append('image', fs.createReadStream(imagePath));

  try {
    const response = await axios.post('http://localhost:8000/analyze-product', form, {
      headers: form.getHeaders(),
    });
    
    // Exact response fields ready for DB storage
    const { product_name, category, tags, description, ocr_text } = response.data;
    console.log("Analysis Result:", { product_name, category, tags, description, ocr_text });
    return response.data;
  } catch (error) {
    console.error("AI Analysis failed:", error.response?.data || error.message);
  }
}
```

### **Python Integration**

```python
import requests

def call_ai_module(image_path: str):
    url = "http://localhost:8000/analyze-product"
    with open(image_path, "rb") as f:
        files = {"image": ("product.jpg", f, "image/jpeg")}
        response = requests.post(url, files=files)
        response.raise_for_status()
        return response.json()
```

---

## ⚙️ Setup & Execution

### 1. **Install Dependencies**

```bash
pip install -r requirements.txt
```

### 2. **Environment Configuration (Optional for Gemini Cloud API)**

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```

*(If no API key is provided, the service operates seamlessly using its built-in Computer Vision & Heuristic NLP engine).*

### 3. **Run the Server**

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive Swagger documentation available at: `http://localhost:8000/docs`

### 4. **Run Automated Tests**

```bash
python test_api.py
```

---

## 📁 Project Structure

```
├── main.py                  # FastAPI application & endpoints
├── ai_engine.py             # Multi-modal AI recognition engine (Gemini API + CV/NLP fallback)
├── ocr_engine.py            # Tesseract OCR & EasyOCR text extraction module
├── schemas.py               # Pydantic request/response schemas
├── config.py                # System path & environment configurations
├── generate_test_images.py # Generator for sample test product images
├── test_api.py              # Automated integration & unit test suite
├── requirements.txt         # Project dependencies
└── README.md                # Documentation & backend contract
```

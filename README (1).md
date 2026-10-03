# Media Pipeline (Cloudinary) - Member 3

Upload -> background removal -> smart crop/resize -> auto format/quality -> tags/metadata -> URLs returned to the backend.

## 1. Setup (VS Code terminal)

```bash
cd media-pipeline
npm install
cp .env.example .env      # Windows: copy .env.example .env
```
Edit `.env` with your Cloudinary credentials (Dashboard -> Settings -> API Keys).

**Enable background removal (one-time):** Cloudinary Dashboard -> Add-ons -> "Cloudinary AI Background Removal" -> Free plan.
Without it the pipeline still works (resize/crop/optimize) and returns `backgroundRemoved: false` plus a warning.

## 2. Verify

```bash
npm run check                                   # tests credentials
npm run test:pipeline -- ./photo.jpg "Red Shoes" footwear   # full pipeline on a local image
npm start                                       # API on http://localhost:5001
```

## 3. API

| Method | Route | Body (multipart/form-data) |
|---|---|---|
| GET | `/api/media/health` | - |
| POST | `/api/media/upload` | `image` (file), `shopId`, `productId`, `name`, `category`, `removeBackground` (default true) |
| POST | `/api/media/upload-bulk` | `images` (up to 20 files), `shopId`, `category`, `removeBackground` |
| DELETE | `/api/media?publicId=...` | - |

Limits: JPG/PNG/WEBP/HEIC/AVIF, 10 MB per file (`MAX_FILE_MB`).

### Response (`POST /upload`)
```json
{
  "success": true,
  "data": {
    "publicId": "smart-catalog/shop-1/products/red-shoes-1a2b3c4d",
    "imageUrl": "https://res.cloudinary.com/.../c_lpad,w_1000,h_1000,b_white/f_auto,q_auto/...",
    "cardUrl": "... 600x600 ...",
    "thumbnailUrl": "... 300x300 smart crop ...",
    "transparentUrl": "... PNG/WebP cutout ...",
    "originalUrl": "...",
    "backgroundRemoved": true,
    "width": 3000, "height": 2000, "format": "jpg", "bytes": 1234567,
    "tags": ["catalog","product","shop-shop-1","category-footwear"],
    "autoTags": [], "dominantColors": ["#c0392b"], "phash": "...",
    "context": { "name": "Red Shoes", "category": "footwear", "shopId": "shop-1", "productId": "" },
    "warnings": []
  }
}
```
Save `imageUrl` (main), `cardUrl`, `thumbnailUrl` and `publicId` (needed for delete) on the product.

## 4. Integrating into the backend

Option A - mount the ready-made routes:
```js
const media = require('./media-pipeline');
app.use('/api/media', media.router);
app.use(media.errorHandler);
```
Option B - call from your own controller:
```js
const { processProductImage } = require('./media-pipeline');
const r = await processProductImage({ buffer: req.file.buffer, shopId, name, category });
product.imageUrl = r.imageUrl; product.thumbnailUrl = r.thumbnailUrl; product.imagePublicId = r.publicId;
```
Frontend example:
```js
const fd = new FormData();
fd.append('image', file); fd.append('shopId', 'shop-1'); fd.append('name', 'Red Shoes');
const { data } = await (await fetch('http://localhost:5001/api/media/upload', { method: 'POST', body: fd })).json();
```

## 5. What happens per image
1. Upload to `smart-catalog/<shopId>/products/` with tags, context metadata, dominant colors, perceptual hash.
2. Eager-generate variants (so first load is instant): main 1000x1000, card 600x600, thumbnail 300x300 (AI smart crop), transparent cutout.
3. All URLs use `f_auto,q_auto` (best format and quality per browser).

## Optional
`ENABLE_AUTO_TAGGING=true` adds Google auto-tagging (needs that add-on) - tags come back in `autoTags`, useful for the AI categorization teammate.

## Troubleshooting
- "Cloudinary is not configured" -> fill `.env`.
- `Invalid Signature` / 401 -> wrong API secret.
- `backgroundRemoved: false` -> enable the background removal add-on (see warning text).
- "Unexpected field name" -> field must be `image` (single) or `images` (bulk).

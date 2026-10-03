import cv2
import numpy as np
from PIL import Image

def analyze_object_bounding_box(pil_image: Image.Image):
    img_rgb = pil_image.convert("RGB")
    img_np = np.array(img_rgb)
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

    # Detect object contours by thresholding non-white / non-light background
    # Background in e-commerce is usually light/white (> 230)
    _, binary = cv2.threshold(gray, 235, 255, cv2.THRESH_BINARY_INV)
    
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        # Get bounding box of the largest contour (the product object)
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Crop to the object
        cropped = img_rgb.crop((x, y, x + w, y + h))
        obj_aspect_ratio = w / float(h)
        
        # Calculate color stats of object crop
        crop_np = np.array(cropped)
        r_avg = np.mean(crop_np[:, :, 0])
        g_avg = np.mean(crop_np[:, :, 1])
        b_avg = np.mean(crop_np[:, :, 2])
        
        return {
            "has_object": True,
            "obj_aspect_ratio": obj_aspect_ratio,
            "crop_w": w,
            "crop_h": h,
            "r_avg": r_avg,
            "g_avg": g_avg,
            "b_avg": b_avg,
            "cropped_img": cropped
        }
    
    return {"has_object": False, "obj_aspect_ratio": pil_image.width / float(pil_image.height)}

if __name__ == "__main__":
    img = Image.open("sample_images/sneakers.png")
    res = analyze_object_bounding_box(img)
    print(f"Object Aspect Ratio after Background Cropping: {res['obj_aspect_ratio']:.2f}")

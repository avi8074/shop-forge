import base64
import os
import sys
import unittest
from fastapi.testclient import TestClient

from main import app

class TestProductIntelligenceAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.required_keys = {"product_name", "category", "tags", "description", "ocr_text"}
        cls.sample_images_dir = "sample_images"

    def test_root_endpoint(self):
        """Test GET / endpoint"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "online")
        self.assertIn("service", data)

    def test_health_endpoint(self):
        """Test GET /health endpoint"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("ocr_engine", data)
        self.assertIn("ai_engine", data)

    def test_analyze_product_multipart_form(self):
        """Test POST /analyze-product with multipart form field 'image' across multiple sample images"""
        image_files = ["beverage_can.jpg", "sneakers.png", "skincare_cream.png", "book_cover.jpg"]

        for img_name in image_files:
            img_path = os.path.join(self.sample_images_dir, img_name)
            self.assertTrue(os.path.exists(img_path), f"Sample image missing: {img_path}")

            with open(img_path, "rb") as f:
                response = self.client.post(
                    "/analyze-product",
                    files={"image": (img_name, f, f"image/{img_name.split('.')[-1]}")}
                )

            self.assertEqual(
                response.status_code, 200, 
                f"Failed for {img_name}: {response.text}"
            )
            data = response.json()

            # Assert exact key structure (NO extra keys, NO missing keys)
            self.assertEqual(
                set(data.keys()), self.required_keys,
                f"Output keys do not match contract exactly for {img_name}. Found: {set(data.keys())}"
            )

            # Assert data types
            self.assertIsInstance(data["product_name"], str)
            self.assertIsInstance(data["category"], str)
            self.assertIsInstance(data["tags"], list)
            self.assertIsInstance(data["description"], str)
            self.assertIsInstance(data["ocr_text"], str)

            # Assert content quality
            self.assertTrue(len(data["product_name"]) > 0, f"Empty product name for {img_name}")
            self.assertTrue(len(data["category"]) > 0, f"Empty category for {img_name}")
            self.assertTrue(len(data["tags"]) > 0, f"Empty tags for {img_name}")
            self.assertTrue(len(data["description"]) > 0, f"Empty description for {img_name}")

            print(f"\n--- Multipart Form Test Success: {img_name} ---")
            print(f"Product Name: {data['product_name']}")
            print(f"Category:     {data['category']}")
            print(f"Tags:         {data['tags']}")
            print(f"Description:  {data['description']}")
            print(f"OCR Text:     {data['ocr_text']}")

    def test_analyze_product_json_base64(self):
        """Test POST /analyze-product with JSON body containing 'image_base64'"""
        img_path = os.path.join(self.sample_images_dir, "beverage_can.jpg")
        with open(img_path, "rb") as f:
            encoded_str = base64.b64encode(f.read()).decode("utf-8")
            data_uri = f"data:image/jpeg;base64,{encoded_str}"

        response = self.client.post(
            "/analyze-product",
            json={"image_base64": data_uri}
        )

        self.assertEqual(response.status_code, 200, f"JSON base64 request failed: {response.text}")
        data = response.json()

        # Assert exact JSON key structure
        self.assertEqual(set(data.keys()), self.required_keys)
        self.assertTrue(len(data["product_name"]) > 0)
        self.assertTrue(len(data["category"]) > 0)

        print(f"\n--- JSON Base64 Payload Test Success ---")
        print(f"Product Name: {data['product_name']}")
        print(f"Category:     {data['category']}")
        print(f"Tags:         {data['tags']}")

    def test_invalid_image_handling(self):
        """Test handling of invalid/corrupt image inputs"""
        response = self.client.post(
            "/analyze-product",
            files={"image": ("corrupt.txt", b"not an image", "text/plain")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid image", response.json()["detail"])

    def test_missing_image_handling(self):
        """Test handling when no image is provided"""
        response = self.client.post("/analyze-product")
        self.assertEqual(response.status_code, 400)
        self.assertIn("No product image provided", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()

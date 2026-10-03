import os
import unittest
from fastapi.testclient import TestClient

from main import app

class TestMediaPipelineEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.sample_image_path = os.path.join("sample_images", "beverage_can.jpg")

    def test_media_health_endpoint(self):
        """Test GET /api/media/health returns service status dictionary"""
        response = self.client.get("/api/media/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("service_online", data)
        self.assertIn("service_url", data)
        self.assertIn("cloudinary_status", data)
        self.assertIn("credentials_configured", data)

    def test_media_upload_validation(self):
        """Test POST /api/media/upload with empty file"""
        response = self.client.post(
            "/api/media/upload",
            files={"image": ("empty.jpg", b"", "image/jpeg")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("empty", response.json()["detail"].lower())

    def test_media_delete_validation(self):
        """Test DELETE /api/media without publicId parameter"""
        response = self.client.delete("/api/media")
        self.assertEqual(response.status_code, 400)
        self.assertIn("publicid", response.json()["detail"].lower())

    def test_analyze_and_process_product(self):
        """Test POST /analyze-and-process-product generates catalog AI data"""
        self.assertTrue(os.path.exists(self.sample_image_path))
        with open(self.sample_image_path, "rb") as f:
            response = self.client.post(
                "/analyze-and-process-product",
                files={"image": ("beverage_can.jpg", f, "image/jpeg")},
                data={"shopId": "test-shop", "removeBackground": "true"}
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("product_name", data)
        self.assertIn("category", data)
        self.assertIn("tags", data)
        self.assertIn("description", data)
        self.assertIn("ocr_text", data)
        self.assertIn("media", data)
        self.assertTrue(len(data["product_name"]) > 0)


if __name__ == "__main__":
    unittest.main()

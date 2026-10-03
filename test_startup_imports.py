import unittest
from fastapi.testclient import TestClient

from main import app


class TestStartupImports(unittest.TestCase):
    def test_main_import_and_health(self):
        with TestClient(app) as client:
            response = client.get('/health')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json().get('status'), 'healthy')

    def test_products_route_is_importable(self):
        with TestClient(app) as client:
            response = client.get('/api/products')
            self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()

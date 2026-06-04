import unittest
from ..main import create_app


class TestMain(unittest.TestCase):
    def test_create_app_returns_fastapi_app(self):
        app = create_app()
        self.assertIsNotNone(app)
        self.assertEqual(app.title, "AI Form Filler")

    def test_app_has_cors_middleware(self):
        app = create_app()
        middleware = [m for m in app.user_middleware]
        cors_middlewares = [m for m in middleware if "CORSMiddleware" in str(m.cls)]
        self.assertEqual(len(cors_middlewares), 1)

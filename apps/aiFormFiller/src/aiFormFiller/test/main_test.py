import unittest
from structlog.testing import capture_logs
from ..main import create_app
from ..context_loader import ContextLoader


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

    def test_create_app_logs_lifecycle(self):
        loader = ContextLoader("missing-cv.txt", "missing-looking-for.txt")
        with capture_logs() as logs:
            create_app(loader)
        events = [entry for entry in logs if entry["event"].startswith("app.")]
        self.assertEqual([entry["event"] for entry in events], ["app.created", "app.context_loaded"])
        self.assertEqual(events[0]["module"], "aiFormFiller.main")
        self.assertEqual(events[0]["log_level"], "info")
        self.assertTrue(events[0]["version"])
        self.assertEqual(events[1]["cv_loaded"], False)
        self.assertEqual(events[1]["looking_for_loaded"], False)
        self.assertEqual(set(events[1]) - {"event", "log_level", "module", "timestamp"}, {"cv_loaded", "looking_for_loaded"})

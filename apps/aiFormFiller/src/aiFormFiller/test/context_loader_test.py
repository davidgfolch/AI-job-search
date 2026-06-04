import os
import tempfile
import time
import unittest
from ..context_loader import ContextLoader


class TestContextLoader(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cv_path = os.path.join(self.temp_dir, "cv.txt")
        self.lf_path = os.path.join(self.temp_dir, "looking-for.txt")
        self.loader = ContextLoader(self.cv_path, self.lf_path)

    def tearDown(self):
        for f in [self.cv_path, self.lf_path]:
            if os.path.exists(f):
                os.remove(f)
        os.rmdir(self.temp_dir)

    def test_load_no_files_returns_false(self):
        result = self.loader.load()
        self.assertFalse(result)

    def test_load_cv_only(self):
        with open(self.cv_path, "w") as f:
            f.write("Experienced Java developer")
        result = self.loader.load()
        self.assertTrue(result)
        self.assertEqual(self.loader.cv_content, "Experienced Java developer")
        self.assertIsNone(self.loader.looking_for_content)

    def test_load_both_files(self):
        with open(self.cv_path, "w") as f:
            f.write("CV content")
        with open(self.lf_path, "w") as f:
            f.write("Salary: 80k")
        result = self.loader.load()
        self.assertTrue(result)
        self.assertEqual(self.loader.cv_content, "CV content")
        self.assertEqual(self.loader.looking_for_content, "Salary: 80k")

    def test_get_context_text_with_both(self):
        with open(self.cv_path, "w") as f:
            f.write("CV content")
        with open(self.lf_path, "w") as f:
            f.write("Salary: 80k")
        self.loader.load()
        text = self.loader.get_context_text()
        self.assertIn("<CV>", text)
        self.assertIn("CV content", text)
        self.assertIn("<LOOKING_FOR>", text)
        self.assertIn("Salary: 80k", text)

    def test_get_context_text_with_cv_only(self):
        with open(self.cv_path, "w") as f:
            f.write("CV content")
        self.loader.load()
        text = self.loader.get_context_text()
        self.assertIn("<CV>", text)
        self.assertNotIn("<LOOKING_FOR>", text)

    def test_reload_if_changed_detects_modification(self):
        with open(self.cv_path, "w") as f:
            f.write("Original")
        self.loader.load()
        self.assertEqual(self.loader.cv_content, "Original")
        time.sleep(0.1)
        with open(self.cv_path, "w") as f:
            f.write("Modified")
        self.loader.reload_if_changed()
        self.assertEqual(self.loader.cv_content, "Modified")

    def test_empty_file_returns_none(self):
        with open(self.cv_path, "w") as f:
            f.write("   ")
        result = self.loader.load()
        self.assertFalse(result)
        self.assertIsNone(self.loader.cv_content)

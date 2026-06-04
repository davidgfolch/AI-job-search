import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from ...main import create_app
from ...context_loader import ContextLoader
from ...test.helpers import TempFiles


class TestApiRoutes(unittest.TestCase):
    def setUp(self):
        self.temp = TempFiles()
        self.loader = ContextLoader(self.temp.cv_path, self.temp.lf_path)
        self.loader.load()
        self.app = create_app(context_loader=self.loader)
        self.client = TestClient(self.app)

    def tearDown(self):
        self.temp.cleanup()

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["cv_loaded"])

    @patch("aiFormFiller.api.routes._service")
    def test_answer_endpoint(self, mock_service):
        mock_service.answer.return_value = MagicMock(text="Tengo 5 años de experiencia con Java", is_clarification=False, provider="local")
        response = self.client.post("/api/answer", json={"question": "¿Años de Java?"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["text"], "Tengo 5 años de experiencia con Java")

    @patch("aiFormFiller.api.routes._service")
    def test_answer_clarification(self, mock_service):
        mock_service.answer.return_value = MagicMock(text="CLARIFICACIÓN: No se encuentra", is_clarification=True, provider="local")
        response = self.client.post("/api/answer", json={"question": "¿Años de Spring Boot 3?"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["type"], "clarification")

    @patch("aiFormFiller.api.routes._service")
    def test_follow_up_endpoint(self, mock_service):
        mock_service.follow_up.return_value = MagicMock(text="Tengo 2 años con Spring Boot 3", is_clarification=False, provider="local")
        response = self.client.post("/api/answer/follow-up", json={"original_question": "Q?", "clarification_answer": "Sí"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["type"], "answer")

    @patch("aiFormFiller.api.routes._service")
    def test_answer_with_custom_provider(self, mock_service):
        mock_service.answer.return_value = MagicMock(text="Answer", is_clarification=False, provider="openai")
        response = self.client.post("/api/answer", json={"question": "Q?", "provider": "openai"})
        self.assertEqual(response.status_code, 200)
        mock_service.answer.assert_called_with("Q?", "openai")

    @patch("aiFormFiller.api.routes._service")
    def test_batch_answer_all_answered(self, mock_service):
        mock_service.answer_batch.return_value = [
            MagicMock(text="5 años", is_clarification=False, provider="local"),
            MagicMock(text="B2", is_clarification=False, provider="local"),
        ]
        response = self.client.post("/api/answer/batch", json={"questions": ["¿Años de Java?", "¿Nivel de inglés?"]})
        data = response.json()
        self.assertEqual(len(data["answers"]), 2)

    @patch("aiFormFiller.api.routes._service")
    def test_batch_answer_mixed_results(self, mock_service):
        mock_service.answer_batch.return_value = [
            MagicMock(text="5 años", is_clarification=False, provider="local"),
            MagicMock(text="CLARIFICACIÓN: No se menciona", is_clarification=True, provider="local"),
        ]
        response = self.client.post("/api/answer/batch", json={"questions": ["Q1?", "Q2?"]})
        data = response.json()
        self.assertEqual(data["answers"][0]["type"], "answer")
        self.assertEqual(data["answers"][1]["type"], "clarification")

    @patch("aiFormFiller.api.routes._service")
    def test_batch_answer_empty_list(self, mock_service):
        mock_service.answer_batch.return_value = []
        response = self.client.post("/api/answer/batch", json={"questions": []})
        self.assertEqual(response.json()["answers"], [])

    def test_health_no_cv_file(self):
        import os
        os.remove(self.temp.cv_path)
        new_loader = ContextLoader(self.temp.cv_path, self.temp.lf_path)
        new_app = create_app(context_loader=new_loader)
        client = TestClient(new_app)
        response = client.get("/api/health")
        self.assertFalse(response.json()["cv_loaded"])

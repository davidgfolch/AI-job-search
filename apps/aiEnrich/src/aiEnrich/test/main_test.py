from unittest.mock import patch


class TestMain:
    @patch('aiEnrich.main.wait_for_db')
    @patch('aiEnrich.main.run_pipeline')
    def test_run(self, mock_pipeline, _mock_wait):
        from ..main import run

        run()

        mock_pipeline.assert_called_once()

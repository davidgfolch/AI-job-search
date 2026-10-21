from unittest.mock import patch


class TestMain:
    @patch('aiEnrich.main.run_pipeline')
    def test_run(self, mock_pipeline):
        from ..main import run

        run()

        mock_pipeline.assert_called_once()

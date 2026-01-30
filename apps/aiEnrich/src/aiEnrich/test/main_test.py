import pytest
from unittest.mock import patch, MagicMock
import sys


class TestMain:
    @patch('aiEnrich.main.AiJobSearchFlow')
    def test_run(self, mock_flow):
        from ..main import run
        
        mock_instance = MagicMock()
        mock_flow.return_value = mock_instance
        
        run()
        
        mock_flow.assert_called_once()
        mock_instance.kickoff.assert_called_once()

    @patch('aiEnrich.main.DataExtractor')
    def test_train_success(self, mock_extractor):
        from ..main import train
        
        mock_crew = MagicMock()
        mock_extractor.return_value.crew.return_value = mock_crew
        
        with patch.object(sys, 'argv', ['script', '5', 'test_file.txt']):
            train()
        
        mock_crew.train.assert_called_once_with(
            n_iterations=5,
            filename='test_file.txt',
            inputs={}
        )

    @patch('aiEnrich.main.DataExtractor')
    def test_train_exception(self, mock_extractor):
        from ..main import train
        
        mock_crew = MagicMock()
        mock_crew.train.side_effect = Exception("Training error")
        mock_extractor.return_value.crew.return_value = mock_crew
        
        with patch.object(sys, 'argv', ['script', '5', 'test_file.txt']):
            with pytest.raises(Exception, match="An error occurred while training the crew: Training error"):
                train()

    @patch('aiEnrich.main.DataExtractor')
    def test_replay_success(self, mock_extractor):
        from ..main import replay
        
        mock_crew = MagicMock()
        mock_extractor.return_value.crew.return_value = mock_crew
        
        with patch.object(sys, 'argv', ['script', 'task_123']):
            replay()
        
        mock_crew.replay.assert_called_once_with(task_id='task_123')

    @patch('aiEnrich.main.DataExtractor')
    def test_replay_exception(self, mock_extractor):
        from ..main import replay
        
        mock_crew = MagicMock()
        mock_crew.replay.side_effect = Exception("Replay error")
        mock_extractor.return_value.crew.return_value = mock_crew
        
        with patch.object(sys, 'argv', ['script', 'task_123']):
            with pytest.raises(Exception, match="An error occurred while replaying the crew: Replay error"):
                replay()

    @patch('aiEnrich.main.DataExtractor')
    def test_test_crew_success(self, mock_extractor_class):
        from ..main import test_crew
        
        mock_crew = MagicMock()
        mock_extractor_class.return_value.crew.return_value = mock_crew
        
        with patch.object(sys, 'argv', ['script', '3', 'gpt-4']):
            test_crew()
        
        mock_crew.test.assert_called_once_with(
            n_iterations=3,
            openai_model_name='gpt-4',
            inputs={}
        )

    @patch('aiEnrich.main.DataExtractor')
    def test_test_crew_exception(self, mock_extractor_class):
        from ..main import test_crew
        
        mock_crew = MagicMock()
        mock_crew.test.side_effect = Exception("Test error")
        mock_extractor_class.return_value.crew.return_value = mock_crew
        
        with patch.object(sys, 'argv', ['script', '3', 'gpt-4']):
            with pytest.raises(Exception, match="An error occurred while replaying the crew: Test error"):
                test_crew()
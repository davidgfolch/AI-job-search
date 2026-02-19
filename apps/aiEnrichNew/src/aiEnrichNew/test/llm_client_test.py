import pytest
from unittest.mock import patch, MagicMock
import sys

# Mocking modules before import if necessary, but patch usually handles it well.
# However, since llm_client imports torch and transformers at top level, 
# we need to ensure they are mocked if we want to run this in an environment without them,
# or just patch them during the test execution. 
# Given the user's environment likely has them, 'patch' is sufficient to avoid heavy loading.

from ..llm_client import get_pipeline, MODEL_ID
from .. import llm_client

@pytest.fixture
def mock_dependencies():
    with patch('aiEnrichNew.llm_client.AutoTokenizer') as mock_tokenizer, \
         patch('aiEnrichNew.llm_client.AutoModelForCausalLM') as mock_model, \
         patch('aiEnrichNew.llm_client.pipeline') as mock_pipeline, \
         patch('aiEnrichNew.llm_client.torch') as mock_torch:
        
        # Setup mocks
        mock_tokenizer.from_pretrained.return_value = MagicMock()
        mock_model.from_pretrained.return_value = MagicMock()
        mock_pipeline_instance = MagicMock()
        mock_pipeline.return_value = mock_pipeline_instance
        
        # Mock cuda availability
        mock_torch.cuda.is_available.return_value = False
        mock_torch.float32 = "float32"
        mock_torch.float16 = "float16"
        
        yield {
            'tokenizer': mock_tokenizer,
            'model': mock_model,
            'pipeline': mock_pipeline,
            'torch': mock_torch,
            'pipeline_instance': mock_pipeline_instance
        }

@patch('aiEnrichNew.llm_client.getEnv')
def test_get_pipeline_initialization(mock_getEnv, mock_dependencies):
    # Mock env vars
    mock_getEnv.side_effect = lambda key, default: default
    
    # Reset singleton
    llm_client._PIPELINE = None
    
    pipeline_instance = get_pipeline()
    
    assert pipeline_instance == mock_dependencies['pipeline_instance']
    
    # Verify tokenizer loading with padding_side='left'
    mock_dependencies['tokenizer'].from_pretrained.assert_called_once_with(MODEL_ID, padding_side='left')
    
    # Verify model loading
    mock_dependencies['model'].from_pretrained.assert_called_once()
    args, kwargs = mock_dependencies['model'].from_pretrained.call_args
    assert args[0] == MODEL_ID
    assert kwargs['device_map'] == "auto"
    
    # Verify pipeline creation
    mock_dependencies['pipeline'].assert_called_once()
    args, kwargs = mock_dependencies['pipeline'].call_args
    assert args[0] == "text-generation"
    assert kwargs['max_new_tokens'] == 2048
    assert kwargs['temperature'] == 0.1
    assert kwargs['top_p'] == 0.9
    assert kwargs['repetition_penalty'] == 1.1
    assert kwargs['batch_size'] == 10

@patch('aiEnrichNew.llm_client.getEnv')
def test_get_pipeline_singleton(mock_getEnv, mock_dependencies):
    mock_getEnv.side_effect = lambda key, default: default
    
    # Reset singleton
    llm_client._PIPELINE = None
    
    # First call
    instance1 = get_pipeline()
    
    # Second call
    instance2 = get_pipeline()
    
    assert instance1 is instance2
    assert instance1 == mock_dependencies['pipeline_instance']
    
    # Ensure initialization only happened once
    mock_dependencies['tokenizer'].from_pretrained.assert_called_once()
    mock_dependencies['model'].from_pretrained.assert_called_once()
    mock_dependencies['pipeline'].assert_called_once()

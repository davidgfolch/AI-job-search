from unittest.mock import patch, MagicMock

from ..llm_client import get_pipeline, MODEL_ID
from .. import llm_client


@patch("aiEnrichSkill.llm_client.AutoTokenizer")
@patch("aiEnrichSkill.llm_client.AutoModelForCausalLM")
@patch("aiEnrichSkill.llm_client.pipeline")
@patch("aiEnrichSkill.llm_client.torch")
def test_get_pipeline_initialization(mock_torch, mock_pipeline, mock_model, mock_tokenizer):
    llm_client._PIPELINE = None
    tokenizer = MagicMock()
    mock_tokenizer.from_pretrained.return_value = tokenizer
    model = MagicMock()
    mock_model.from_pretrained.return_value = model
    pipeline_instance = MagicMock()
    mock_pipeline.return_value = pipeline_instance
    mock_torch.cuda.is_available.return_value = False
    mock_torch.float32 = "float32"
    mock_torch.float16 = "float16"

    result = get_pipeline()

    assert result == pipeline_instance
    mock_tokenizer.from_pretrained.assert_called_once_with(MODEL_ID, padding_side='left')
    mock_model.from_pretrained.assert_called_once()
    args, kwargs = mock_model.from_pretrained.call_args
    assert args[0] == MODEL_ID
    assert kwargs['device_map'] == "auto"
    mock_pipeline.assert_called_once()
    args, kwargs = mock_pipeline.call_args
    assert args[0] == "text-generation"
    assert kwargs['max_new_tokens'] == 2048
    assert kwargs['temperature'] == 0.1
    assert kwargs['top_p'] == 0.9
    assert kwargs['repetition_penalty'] == 1.1
    assert kwargs['batch_size'] == 10


@patch("aiEnrichSkill.llm_client.AutoTokenizer")
@patch("aiEnrichSkill.llm_client.AutoModelForCausalLM")
@patch("aiEnrichSkill.llm_client.pipeline")
@patch("aiEnrichSkill.llm_client.torch")
def test_get_pipeline_singleton(mock_torch, mock_pipeline, mock_model, mock_tokenizer):
    llm_client._PIPELINE = None
    tokenizer = MagicMock()
    mock_tokenizer.from_pretrained.return_value = tokenizer
    model = MagicMock()
    mock_model.from_pretrained.return_value = model
    pipeline_instance = MagicMock()
    mock_pipeline.return_value = pipeline_instance
    mock_torch.cuda.is_available.return_value = False
    mock_torch.float32 = "float32"
    mock_torch.float16 = "float16"

    instance1 = get_pipeline()
    instance2 = get_pipeline()

    assert instance1 is instance2
    mock_tokenizer.from_pretrained.assert_called_once()
    mock_model.from_pretrained.assert_called_once()
    mock_pipeline.assert_called_once()


@patch("aiEnrichSkill.llm_client.AutoTokenizer")
@patch("aiEnrichSkill.llm_client.AutoModelForCausalLM")
@patch("aiEnrichSkill.llm_client.pipeline")
@patch("aiEnrichSkill.llm_client.torch")
def test_get_pipeline_pad_token_set(mock_torch, mock_pipeline, mock_model, mock_tokenizer):
    llm_client._PIPELINE = None
    tokenizer = MagicMock()
    tokenizer.pad_token = None
    tokenizer.eos_token = "<eos>"
    mock_tokenizer.from_pretrained.return_value = tokenizer
    model = MagicMock()
    mock_model.from_pretrained.return_value = model
    mock_pipeline.return_value = MagicMock()
    mock_torch.cuda.is_available.return_value = False
    mock_torch.float32 = "float32"
    mock_torch.float16 = "float16"

    get_pipeline()

    assert tokenizer.pad_token == "<eos>"


@patch("aiEnrichSkill.llm_client.AutoTokenizer")
@patch("aiEnrichSkill.llm_client.AutoModelForCausalLM")
@patch("aiEnrichSkill.llm_client.pipeline")
@patch("aiEnrichSkill.llm_client.torch")
def test_get_pipeline_cuda_available(mock_torch, mock_pipeline, mock_model, mock_tokenizer):
    llm_client._PIPELINE = None
    tokenizer = MagicMock()
    mock_tokenizer.from_pretrained.return_value = tokenizer
    model = MagicMock()
    mock_model.from_pretrained.return_value = model
    mock_pipeline.return_value = MagicMock()
    mock_torch.cuda.is_available.return_value = True
    mock_torch.float32 = "float32"
    mock_torch.float16 = "float16"

    get_pipeline()

    call_kwargs = mock_model.from_pretrained.call_args[1]
    assert call_kwargs['dtype'] == "float16"

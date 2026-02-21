import pytest
import gc
import torch
from aiEnrich3.services.extractors.salary_extractor import SalaryExtractor

@pytest.fixture(scope="module")
def extractor():
    model = SalaryExtractor()
    yield model
    # Clean up to prevent pytest from hanging on background torch threads
    del model
    gc.collect()
    # If using PyTorch on CPU, sometimes it's needed to clear threading issues
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

@pytest.mark.parametrize("text, expected_found", [
    ("The salary is 50.000€ per year.", True),
    ("We offer between $50k - $60k depending on experience.", True),
    ("Competitive compensation up to 120,000 yearly.", True),
    ("Salario de 40.000 a 50.000 euros brutos anuales.", True),
    ("This job does not specify how much they pay.", False)
])
def test_extract_salary(extractor, text, expected_found):
    result = extractor.extract(text)
    
    if not expected_found:
        assert result is None
    else:
        assert result is not None
        assert len(result) > 0

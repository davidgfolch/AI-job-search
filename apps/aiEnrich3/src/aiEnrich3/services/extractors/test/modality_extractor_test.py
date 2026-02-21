import pytest
import gc
import torch
from aiEnrich3.services.extractors.modality_extractor import ModalityExtractor
from aiEnrich3.domain.entities import ModalityType

@pytest.fixture(scope="module")
def extractor():
    model = ModalityExtractor()
    yield model
    # Clean up to prevent pytest from hanging on background threads
    # (Same as GLiNER fixture cleanup)
    del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

@pytest.mark.parametrize("text, expected", [
    ("This is a fully remote position based anywhere in the US.", ModalityType.REMOTE),
    ("You must come to our Madrid office 3 days a week (hybrid).", ModalityType.HYBRID),
    ("El trabajo es 100% presencial en nuestras oficinas de Barcelona.", ModalityType.ON_SITE),
    ("Trabajo en remoto con horario flexible.", ModalityType.REMOTE),
    ("Modèle hybride: 2 jours en télétravail, 3 jours sur site.", ModalityType.HYBRID),
    ("We are looking for a senior developer. Excellent benefits.", None)  # No modality specified
])
def test_extract_modality(extractor, text, expected):
    result = extractor.extract(text)
    assert result == expected

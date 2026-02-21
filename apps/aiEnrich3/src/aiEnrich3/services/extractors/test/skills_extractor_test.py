import pytest
import gc
import torch
from aiEnrich3.services.extractors.skills_extractor import SkillsExtractor

@pytest.fixture(scope="module")
def extractor():
    model = SkillsExtractor()
    yield model
    # Clean up to prevent pytest from hanging on background torch threads
    del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

@pytest.mark.parametrize("text, expected_required_subset, expected_optional_subset", [
    (
        "Requirements: 3 years of Python and React. Nice to have: Docker and Kubernetes.",
        ["python", "react"],
        ["docker", "kubernetes"]
    ),
    (
        "Se requiere experiencia en Java y Spring Boot. Valorable conocimientos en AWS.",
        ["java", "spring boot"],
        ["aws"]
    ),
    (
        "Compétences exigées : maîtrise de TypeScript. Un plus: expérience avec GraphQL.",
        ["typescript"],
        ["graphql"]
    ),
    (
        "This is an administrative role requiring communication skills and MS Office.",
        ["ms office"],  # GLiNER usually picks up specific concrete tools better than abstract "communication skills"
        []
    )
])
def test_extract_skills(extractor, text, expected_required_subset, expected_optional_subset):
    required, optional = extractor.extract(text)
    
    # We check for subsets rather than exact matches because GLiNER might extract extra items 
    # (e.g. "3 years", "experiencia", or split pieces) that we didn't explicitly assert, 
    # but it should definitely find our core skills.
    
    for r_skill in expected_required_subset:
        # Check if the expected skill is a substring of any extracted required skill 
        # (GLiNER might extract "Python programming" instead of just "Python")
        assert any(r_skill in extracted for extracted in required), \
            f"Expected required skill '{r_skill}' not found in {required}"
            
    for o_skill in expected_optional_subset:
        assert any(o_skill in extracted for extracted in optional), \
            f"Expected optional skill '{o_skill}' not found in {optional}"

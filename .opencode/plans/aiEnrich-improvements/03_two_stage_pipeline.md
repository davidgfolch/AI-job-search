# Plan C: Two-Stage Pipeline (aiEnrich3 Fast Path + aiEnrich LLM Fallback)

## Goal

Run aiEnrich3 (GLiNER/mDeBERTa, ~0.5-2s per job) first, then only invoke the slow Ollama LLM for fields where aiEnrich3 has low confidence.

## Rationale

aiEnrich3 is already in your repo and is **10-20x faster** than the Ollama LLM. Many job descriptions have clear salary ranges, explicit technology lists, and obvious modality keywords that specialized NER/classification models handle correctly. Full LLM inference is overkill for every single field of every job.

## Architecture

```
New job text
  │
  ├─ [Stage 1] aiEnrich3 pipeline (GLiNER + mDeBERTa)
  │     ↓
  │   For each field: {value, confidence}
  │     ├─ salary.confidence >= 0.7  → keep
  │     ├─ skills.confidence >= 0.7  → keep (for each skill)
  │     └─ modality.confidence >= 0.4 → keep (already low bar)
  │
  ├─ [Stage 2] Only for low-confidence fields:
  │     Build targeted Ollama prompt for missing fields only
  │     {"fields": ["salary"], "text": "..."}
  │     → parse only the requested fields from LLM response
  │
  └─ Merge results → save to DB
```

## Files to Modify

### `apps/aiEnrich3/src/aiEnrich3/pipeline.py`

Add a method that returns per-field confidence scores alongside values:

```python
def process_job_with_confidence(self, text: str) -> dict:
    """
    Returns:
    {
        "salary": {"value": "80k-90k", "confidence": 0.85},
        "required_skills": {"value": ["python", "java"], "confidence": 0.72},
        "optional_skills": {"value": ["docker"], "confidence": 0.65},
        "modality": {"value": "REMOTE", "confidence": 0.91}
    }
    """
```

- For GLiNER extractions: use the entity's `score` field averaged across entities of that type
- For modality: use the classifier's `top_score`

### `apps/aiEnrich/src/aiEnrich/hybrid_extractor.py` (new)

Orchestrates the two stages:

```python
def hybrid_extract(text: str, threshold: float = 0.7) -> dict:
    # Stage 1: fast pipeline
    fast_result = aiEnrich3_pipeline.process_job_with_confidence(text)
    
    # Identify low-confidence fields
    missing_fields = [f for f in ["salary", "modality", "skills"] 
                      if fast_result[f]["confidence"] < threshold]
    
    if not missing_fields:
        return extract_values(fast_result)
    
    # Stage 2: targeted LLM prompt
    llm_result = query_ollama_for_fields(text, missing_fields)
    
    return merge(fast_result, llm_result)
```

### `apps/aiEnrich/src/aiEnrich/dataExtractor.py`

- Replace the pure CrewAI/LLM extraction with `hybrid_extract()`
- The rest of the flow (save, error handling, retry) stays the same

### `apps/aiEnrich/pyproject.toml`

Add aiEnrich3 as a dependency:

```toml
[tool.uv.sources]
aiEnrich3 = { path = "../aiEnrich3", editable = true }

[project.dependencies]
aiEnrich3 = "0.1.0"
```

## Key Design Decisions

### Targeted LLM Prompts

Instead of asking the LLM to extract everything, build a minimal prompt for only the missing fields:

```python
def build_fallback_prompt(text: str, missing_fields: list[str]) -> str:
    field_instructions = {
        "salary": "- salary: The salary information ONLY if explicitly stated",
        "modality": "- modality: Must be exactly REMOTE, HYBRID, or ON_SITE",
        "skills": "- required_technologies: comma-separated list\n- optional_technologies: comma-separated list",
    }
    instructions = "\n".join(field_instructions[f] for f in missing_fields)
    return f"""Extract ONLY these fields from the job below:
{instructions}

Job:
{text[:4000]}

Return ONLY a JSON object with the requested fields:
{{"""
```

This is **shorter input + shorter output** → 2-3x faster LLM call than the full extraction.

### Threshold Tuning

| Field | Starting Threshold | Rationale |
|-------|-------------------|-----------|
| Salary | 0.7 | GLiNER is precise on numeric entities |
| Skills | 0.6 | Skills can be ambiguous, be more permissive |
| Modality | 0.4 | mDeBERTa already has a low bar |

Monitor logs for confidence scores and adjust.

## Quality Considerations

- If aiEnrich3 is confident in all fields, **no LLM call happens** → fastest path, no quality change
- If aiEnrich3 has low confidence, the LLM still handles those fields → quality same as current
- Hybrid mode can be toggled via env var (e.g., `AI_ENRICH_HYBRID=true`) for easy rollback

## Rollback

- Set `AI_ENRICH_HYBRID=false` → reverts to pure LLM (no code change needed)
- Or revert `dataExtractor.py` to previous version
- Delete `hybrid_extractor.py`

## Implementation Order

1. Add `process_job_with_confidence()` to aiEnrich3 pipeline
2. Create `hybrid_extractor.py` in aiEnrich
3. Wire it into `dataExtractor.py`
4. Add aiEnrich3 dependency to `pyproject.toml`
5. Run `uv sync` + test both paths (fast path only, LLM fallback, mixed)

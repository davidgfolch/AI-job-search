# Plan E: Prompt & Token Optimization (Quick Wins)

## Goal

Reduce per-job inference time by 2-3x through smarter input/output token management, without changing the model or architecture.

## Rationale

LLM inference time scales roughly linearly with total tokens (input + output). Currently:

| Metric | Current Value | Problem |
|--------|--------------|---------|
| Input tokens | ~2000-4000 (full markdown) | Contains boilerplate, navigation, irrelevant sections |
| Output tokens | ~2048 (max) | JSON result needs ~50-100 tokens max |
| JSON format | Unstructured, parsed with regex | Retries on malformed output waste time |

## Sub-Plans

### E.1: Reduce Output Tokens (`num_predict`)

Force Ollama to generate a short JSON response:

```python
# In ollama_client.py (Plan A):
response = requests.post(f"{base_url}/api/generate", json={
    "model": model,
    "prompt": prompt,
    "stream": False,
    "format": "json",          # Ollama JSON mode
    "options": {
        "temperature": 0,
        "num_predict": 256,     # Down from 2048
    }
})
```

**Gain:** ~2x faster generation (256 vs 2048 tokens, and JSON mode avoids retries)

### E.2: Input Compression

Instead of sending the full markdown, extract the relevant sections:

```python
def compress_job_text(title: str, markdown: str, max_chars: int = 3000) -> str:
    sections = []
    sections.append(f"Title: {title}")
    
    # Always keep the first 1500 chars (usually contains summary + requirements)
    sections.append(markdown[:1500])
    
    # Extract salary-related lines
    for line in markdown.split('\n'):
        if any(kw in line.lower() for kw in ['€', '$', 'salary', 'sueldo', 'salario', 'k', 'remuneration']):
            sections.append(f"[Salary]: {line[:200]}")
    
    # Extract modality-related lines
    for line in markdown.split('\n'):
        if any(kw in line.lower() for kw in ['remote', 'hybrid', 'presencial', 'teletrabajo', 'remoto', 'híbrido', 'on-site', 'onsite']):
            sections.append(f"[Modality]: {line[:200]}")
    
    # Extract technology sections
    for line in markdown.split('\n'):
        if any(kw in line.lower() for kw in ['technolog', 'skill', 'requirement', 'stack', 'tool', 'lenguaje', 'tecnología', 'conocimiento']):
            sections.append(f"[Tech]: {line[:300]}")
    
    combined = '\n'.join(sections)
    return combined[:max_chars]
```

**Gain:** 2-3x reduction in input tokens (typically 4000 → 1500)

### E.3: Ollama JSON Mode

The prompt asks for JSON, but Ollama's native `format: "json"` enforces it at the engine level:

```python
# In ollama_client.py:
response = requests.post(url, json={
    "model": model,
    "prompt": prompt,
    "format": "json",  # Forces valid JSON output
    "options": {"temperature": 0, "num_predict": 256}
})
```

This eliminates:
- Malformed JSON responses (no more regex fixup)
- Hallucinated markdown code blocks
- Extra conversational text

**Gain:** ~20% time saved from avoiding retries/fixups

### E.4: Optimized Prompt Template

Current prompt (from `tasks.yaml`) has redundant boilerplate. Compact version:

```
Extract from this job offer as JSON:
{
  "required_technologies": "comma-separated or empty",
  "optional_technologies": "comma-separated or empty",
  "salary": "text or null",
  "modality": "REMOTE|HYBRID|ON_SITE|null"
}
---JOB---
{compressed_text}
---JSON---
```

This is ~50% shorter than the current prompt while conveying the same instructions.

### E.5: Disable Skill Enrichment in Main Loop

Your `.env.example` already has `AI_ENRICH_SKILL='false'`. Ensure the loop respects this cleanly:

```python
# In crew.py:
while True:
    if dataExtractor() > 0:
        continue
    if get_skill_enabled() and skillEnricher() > 0:
        continue
    # ...
```

## Files to Modify

| Change | File | Effort |
|--------|------|--------|
| E.1 + E.3 | `ollama_client.py` (new, from Plan A) or `dataExtractor.py` | 10 min |
| E.2 | `dataExtractor.py` — add `compress_job_text()` function | 30 min |
| E.4 | `dataExtractor.py` — update prompt template | 10 min |
| E.5 | `crew.py` — verify skill enrichment flag | 5 min |

## Dependencies

None. All changes are pure Python/logic.

## Quality Considerations

- **Input compression**: Must be tested against real jobs to ensure key info isn't lost. The safe approach: keep first N chars (usually the most informative), then add targeted section extraction as a bonus.
- **JSON mode**: Ollama's JSON mode constrains the model to produce valid JSON. This may occasionally cause empty/null fields where the current regex-based parser would have extracted partial info. Compare outputs side by side for 50 jobs.
- **Reduced output tokens**: With `num_predict=256`, the model has ample room for a brief JSON response (~50-100 tokens). No degradation expected.

## Verification

Create a comparison script:

```python
# scripts/compare_enrichment.py
# Runs old (CrewAI) and new (direct Ollama + optimizations) on the same 20 jobs
# Compares output fields, measures time per job
# Reports: time savings, field match rate, differences
```

## Rollback

- Revert `dataExtractor.py` to previous prompt template
- Remove the `compress_job_text()` function
- Set `num_predict` back to default (or remove the option entirely)
- Remove `format: "json"` from Ollama request

## Implementation Order

1. Implement E.3 (JSON mode) — lowest effort, instant gain
2. Implement E.1 (num_predict=256) — single param change
3. Implement E.4 (optimized prompt) — one string change
4. Implement E.2 (input compression) — new function, test thoroughly
5. Run comparison script to validate quality

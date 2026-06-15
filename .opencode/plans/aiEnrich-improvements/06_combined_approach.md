# Plan F: Combined / Recommended Approach

## Goal

Stack all individual plans together for maximum speedup (10-20x) while maintaining extraction quality.

## Architecture

```
New job from DB
  │
  ├─ (optional) [FAISS RAG cache] ── hit? ──→ reuse cached result
  │                                       ── miss?
  │                                            │
  │                                            v
  │                              (optional) [aiEnrich3 fast path]
  │                                            │
  │                                   ┌────────┴────────┐
  │                                   │ high confidence  │ low confidence
  │                                   │ for all fields   │ for some fields
  │                                   v                  v
  │                              Save result        [Direct Ollama API]
  │                                                   │
  │                                              Compressed prompt
  │                                              JSON mode
  │                                              256 output tokens
  │                                                   │
  │                                              Parse result
  │                                                   │
  │                                              Merge with fast path
  │                                                   │
  │                                                   v
  │                                            Store in FAISS cache
  │                                                   │
  └────────────────────────────────────────────── Save to DB
```

## Implementation Phases

### Phase 1: Low Effort, High Impact (1 session)

**Plans:** E (prompt optimization) + A (direct Ollama)

Deliverable: `aiEnrich` without CrewAI, with JSON mode, compressed input, optimized prompt, reduced output tokens.

| Step | Change | Files | Time |
|------|--------|-------|------|
| 1 | Create `ollama_client.py` | New file | 30 min |
| 2 | Rewrite `dataExtractor.py` | Remove CrewBase, use direct Ollama | 1 hr |
| 3 | Simplify `crew.py` | Remove Flow decorator | 15 min |
| 4 | Add prompt compression | New function in dataExtractor | 30 min |
| 5 | Add JSON mode + num_predict | In ollama_client.py | 5 min |

**Expected speedup:** 3-5x  
**Quality:** Unchanged (same model, same prompt intent)

### Phase 2: RAG Cache (1 session)

**Plan:** B (FAISS cache)

Deliverable: Persistent cache that skips LLM inference for similar jobs.

| Step | Change | Files | Time |
|------|--------|-------|------|
| 1 | Create `embedding_service.py` | New file | 30 min |
| 2 | Create `rag_cache.py` | New file | 1 hr |
| 3 | Hook cache into `dataExtractor.py` | Modify _process_job_safe | 30 min |
| 4 | Init/persist cache in `crew.py` | Modify main loop | 15 min |

**Expected speedup:** 5-10x cumulative (cache hit rate ~50% after first week)

### Phase 3: Two-Stage Pipeline (1-2 sessions)

**Plan:** C (aiEnrich3 fast path)

Deliverable: aiEnrich3 extraction with LLM fallback for low-confidence fields.

| Step | Change | Files | Time |
|------|--------|-------|------|
| 1 | Add confidence output to aiEnrich3 pipeline | Modify pipeline.py | 30 min |
| 2 | Create `hybrid_extractor.py` | New file | 1.5 hr |
| 3 | Wire into `dataExtractor.py` | Replace extraction call | 15 min |
| 4 | Add aiEnrich3 dependency | pyproject.toml | 5 min |

**Expected speedup:** 10-20x cumulative (most jobs handled by fast path)

## Configuration

Environment variables to control the pipeline:

```bash
# In .env or .env.secrets

# Phase 1: Direct Ollama
AI_ENRICH_USE_DIRECT_API=true       # Enable direct API (skip CrewAI)
AI_ENRICH_JSON_MODE=true            # Force JSON format
AI_ENRICH_MAX_PREDICT=256           # Max output tokens

# Phase 2: RAG Cache
AI_ENRICH_RAG_CACHE=true            # Enable FAISS cache
AI_ENRICH_RAG_THRESHOLD=0.95        # Similarity threshold
AI_ENRICH_RAG_CACHE_PATH=cache/     # Cache directory

# Phase 3: Hybrid pipeline
AI_ENRICH_HYBRID=true               # Enable two-stage pipeline
AI_ENRICH_HYBRID_THRESHOLD=0.7      # Confidence threshold for fast path
```

All default to `false`/disabled — opt-in per phase.

## Testing Strategy

### Per-Phase Validation

Each phase should validate:

1. **Speed**: Time per job (average over 50 jobs)
2. **Quality**: Field-by-field comparison with baseline (CrewAI output)
3. **Error rate**: Number of failed/malformed enrichments

### Comparison Script

Create `scripts/compare_enrichment.py`:

```bash
# Usage
python scripts/compare_enrichment.py --baseline=baseline_results.json --new=new_results.json

# Output
Field match rates:
  salary:          98% (baseline) vs 97% (new) — 1% regression
  required_tech:   95% vs 96% — 1% improvement
  optional_tech:   82% vs 80% — 2% regression
  modality:        99% vs 99% — unchanged

Speed: 12.4s avg (baseline) vs 2.1s (new) — 5.9x faster
```

### Gradual Rollout

```python
# In dataExtractor.py, use a sampling approach:
import random
sample_rate = float(getEnv("AI_ENRICH_NEW_FLOW_SAMPLE_RATE", "0.0"))

if random.random() < sample_rate:
    new_result = fast_extract(job)  # use the new pipeline
    old_result = old_extract(job)   # also run old for comparison
    log_comparison(job.id, old_result, new_result)
    save(new_result)                # new result wins
```

Start with `sample_rate=0.1` (10% of jobs), compare results, then ramp up.

## Rollback Strategy

Every phase is independently revertible:

| Phase | Rollback Method |
|-------|----------------|
| 1 | Set `AI_ENRICH_USE_DIRECT_API=false` or revert 4 files |
| 2 | Set `AI_ENRICH_RAG_CACHE=false` or revert 3 files |
| 3 | Set `AI_ENRICH_HYBRID=false` or revert 3 files |

## Performance Budget

Target: **< 2 seconds per job average** on your CPU-only machine.

| Phase | Time per job (est.) | Cumulative speedup |
|-------|--------------------|--------------------|
| Baseline (current) | ~15s | 1x |
| After Phase 1 | ~4s | ~4x |
| After Phase 2 | ~2s (with 50% cache hit) | ~8x |
| After Phase 3 | ~1s (most jobs via fast path) | ~15x |

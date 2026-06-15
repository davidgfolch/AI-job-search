# AI Enrichment — Speed Improvement Plans

## Context

You have 3 enrichment modules. You primarily use **aiEnrich** (CrewAI + Ollama) because it gives the best extraction quality, but it's the slowest (~10-30s/job on CPU). These plans focus on making it faster while preserving quality.

## Modules Overview

| Module | Approach | Speed | Quality |
|--------|----------|-------|---------|
| **aiEnrich** | CrewAI + Ollama (`qwen2.5:3b`) | Slow (10-30s/job) | Best |
| **aiEnrichNew** | HF Transformers (`Qwen2.5-1.5B`) | Moderate (5-15s/job) | Good |
| **aiEnrich3** | GLiNER + mDeBERTa + Regex | Fast (0.5-2s/job) | Moderate |

## Plans Index

| # | File | Plan | Effort | Speedup | Quality Impact |
|---|------|------|--------|---------|---------------|
| 1 | `01_direct_ollama_api.md` | Replace CrewAI with direct Ollama API | Low | ~1.3x | None (same model/prompt) |
| 2 | `02_rag_cache.md` | FAISS similarity cache to skip LLM | Medium | 2-5x effective | None (reuses own results) |
| 3 | `03_two_stage_pipeline.md` | aiEnrich3 fast path + LLM fallback | Medium | 3-8x | Minor (only on low-conf fields) |
| 4 | `04_gguf_quantization.md` | llama-cpp-python for aiEnrichNew | Medium | 3-5x | None (same model, quantized) |
| 5 | `05_prompt_optimization.md` | Token reduction, JSON mode, input compression | Low | 2-3x | None |
| 6 | `06_combined_approach.md` | All plans stacked together | High | 10-20x | Negligible |

## Recommended Order

Build incrementally, each step is independent:

```
Step 1: 05_prompt_optimization.md  +  01_direct_ollama_api.md
              ↓
Step 2: 02_rag_cache.md
              ↓
Step 3: 03_two_stage_pipeline.md
```

Each step can be deployed and tested independently. Rollback is straightforward (revert the changed files).

# Plan B: RAG Cache Layer (Skip LLM Inference for Similar Jobs)

## Goal

Avoid running LLM inference on jobs that are very similar to already-enriched ones by using embedding similarity search.

## Rationale

Job boards repost similar positions from the same or similar companies. If a job description has 95%+ semantic similarity to one already enriched, running the LLM again is wasteful. The same model used in `aiCvMatcher` (`all-MiniLM-L6-v2`) can compute embeddings fast on CPU (~50ms per job).

## Architecture

```
New job
  │
  ├─ compute embedding (all-MiniLM-L6-v2) ─→ FAISS search
  │                                              │
  │                                   ┌──────────┴──────────┐
  │                                   │ similarity > 0.95   │ similarity ≤ 0.95
  │                                   │                      │
  │                                   v                      v
  │                              Reuse cached             Run Ollama
  │                              result                   enrichment
  │                                   │                      │
  │                                   │                      v
  │                                   │               Store result + embedding
  │                                   │               in FAISS index
  │                                   v                      │
  └────────────────────────────── Save to DB ←──────────────┘
```

## Files to Create

### `apps/aiEnrich/src/aiEnrich/rag_cache.py`

Persistence layer for the FAISS index + enrichment results:

```python
class EnrichmentCache:
    def __init__(self, index_path: str = "cache/faiss.index", data_path: str = "cache/results.pkl")
    def search(self, embedding: np.ndarray, threshold: float = 0.95) -> dict | None
    def add(self, embedding: np.ndarray, result: dict)
    def save()
    def load()
    @property
    def size(self) -> int
```

- Uses `faiss.IndexFlatIP(384)` (Inner Product = cosine similarity when vectors are normalized)
- Stores results in a parallel `list[dict]` indexed by FAISS position
- Persists index to disk via `faiss.write_index()` + `pickle`
- Singleton pattern (same as `FastCVMatcher`)

### `apps/aiEnrich/src/aiEnrich/embedding_service.py`

```python
class EmbeddingService:
    _model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def encode(text: str) -> np.ndarray
    def encode_job(title: str, markdown: str) -> np.ndarray
    def normalize(embedding: np.ndarray) -> np.ndarray
```

- Wraps the sentence transformer
- Normalizes embeddings for cosine similarity
- Singleton pattern, lazy-loaded

## Files to Modify

### `apps/aiEnrich/src/aiEnrich/dataExtractor.py`

- After fetching job data, compute embedding → search cache
- If cache hit: log "RAG cache hit (similarity: {score})" → save result directly, skip LLM
- If cache miss: run LLM → add embedding + result to cache

```python
# Pseudocode for the modified _process_job_safe
embedding = embedder.encode_job(title, markdown)
cached = cache.search(embedding)
if cached:
    result = cached
    print(green(f'RAG cache hit id={id} (similarity={score:.3f})'))
else:
    result = query_ollama(prompt)  # or current LLM call
    cache.add(embedding, result)   # store for future
_save(repo, id, result)
```

### `apps/aiEnrich/src/aiEnrich/crew.py`

- Initialize `EnrichmentCache` and `EmbeddingService` at startup
- Call `cache.load()` to restore previous state
- Call `cache.save()` on graceful exit or periodically (every 100 jobs)

### `apps/aiEnrich/pyproject.toml`

```diff
+ faiss-cpu>=1.8.0
+ sentence-transformers>=2.3.0
```

## Dependencies

- `faiss-cpu` — vector similarity search
- `sentence-transformers` — embedding model (already used by `aiCvMatcher` in the same project)

## Quality Considerations

- **Threshold tuning**: Start with 0.95 (very strict). Monitor false positives and adjust down to 0.90 if coverage is too low.
- **Exact match is guaranteed**: The cache returns results from previously-successful Ollama runs, so quality is identical to what the LLM would produce.
- **Confidence logging**: Log every cache hit with similarity score for monitoring.
- **Cache invalidation**: None needed — enrichment results don't become stale. Jobs are enriched once.

## Storage

- FAISS index: `apps/aiEnrich/cache/faiss.index` (~1MB per 10K entries)
- Results pickle: `apps/aiEnrich/cache/results.pkl` (~100KB per 10K entries)
- Memory: ~15MB for 10K embeddings (384-dim float32) + 384KB FAISS index
- Create `apps/aiEnrich/cache/.gitkeep` to ensure directory exists

## Rollback

- Remove embedding/RAG calls from `dataExtractor.py`
- Delete `rag_cache.py`, `embedding_service.py`
- Remove `faiss-cpu`, `sentence-transformers` from `pyproject.toml`
- Cache files on disk can be kept for later use

## Implementation Order

1. Create `embedding_service.py` (standalone, easy to test)
2. Create `rag_cache.py` (depends on embeddings)
3. Modify `dataExtractor.py` to hook into the cache
4. Modify `crew.py` to init/persist cache
5. Run `uv sync` + test

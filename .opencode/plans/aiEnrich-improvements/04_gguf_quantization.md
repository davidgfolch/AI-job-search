# Plan D: GGUF Quantized Models via llama-cpp-python

## Goal

Replace Hugging Face Transformers with `llama-cpp-python` in `aiEnrichNew` for CPU-optimized inference, making it a viable faster alternative to `aiEnrich` (Ollama) if quality is acceptable.

## Rationale

`llama.cpp` is the gold standard for CPU inference:
- **4-bit quantization** reduces model memory by ~4x (1.5B model: 6GB → 750MB)
- **CPU-optimized kernels** (AVX2, AVX-512, ARM NEON) give 2-5x speedup over vanilla PyTorch
- Used by Ollama under the hood — same engine, direct bindings

**Note:** This is an optimization for `aiEnrichNew`, not `aiEnrich` (which already uses Ollama/llama.cpp). Use this if you want `aiEnrichNew` to be a faster drop-in replacement with comparable quality.

## Architecture

```
Before (aiEnrichNew):
  Job text → AutoTokenizer → AutoModelForCausalLM (float32, 6GB) → pipeline() → result

After (aiEnrichNew + llama-cpp):
  Job text → llama_cpp.Llama tokenizer → Llama (Q4_K_M, 750MB) → create_completion() → result
```

## Files to Modify

### `apps/aiEnrichNew/src/aiEnrichNew/llm_client.py`

Complete rewrite:

```python
import os
from llama_cpp import Llama
from commonlib.environmentUtil import getEnv

MODEL_REPO = "Qwen/Qwen2.5-1.5B-Instruct-GGUF"
MODEL_FILE = "qwen2.5-1.5b-instruct-q4_k_m.gguf"
_PIPELINE = None

def get_pipeline():
    global _PIPELINE
    if _PIPELINE is None:
        model_path = _ensure_model_downloaded()
        _PIPELINE = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_threads=os.cpu_count(),
            n_gpu_layers=0,          # CPU only
            verbose=False,
        )
    return _PIPELINE

def _ensure_model_downloaded() -> str:
    # Auto-download GGUF from Hugging Face Hub on first run
    from huggingface_hub import hf_hub_download
    return hf_hub_download(repo_id=MODEL_REPO, filename=MODEL_FILE)
```

### `apps/aiEnrichNew/src/aiEnrichNew/llm_utils.py`

Update `process_batch()` to use `llama_cpp`'s API:

```python
# Instead of pipeline(prompts, batch_size=len(prompts))
# llama-cpp-python supports create_chat_completion for single items
# Process items in sequence (still faster than HF Transformers)

for prompt in prompts:
    output = pipeline.create_chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=256,
        temperature=0.1,
    )
    generated_text = output["choices"][0]["message"]["content"]
```

Alternatively, if the original `pipeline()` API compatibility is needed, wrap the `Llama` instance in a callable class.

### `apps/aiEnrichNew/pyproject.toml`

```diff
- transformers>=4.40.0
- torch>=2.2.0
- accelerate>=0.29.0
+ llama-cpp-python>=0.2.80
+ huggingface-hub>=0.23.0
```

## Performance Comparison (1.5B model on CPU)

| Metric | HF Transformers | llama-cpp (Q4_K_M) |
|--------|----------------|-------------------|
| Memory usage | ~6 GB | ~750 MB |
| Tokens/sec | ~5-10 | ~20-40 |
| Model load time | ~30s | ~5-10s |
| Per-job time | ~5-15s | ~1-4s |

## Quality Impact

- **4-bit quantization** has negligible quality loss for extraction tasks (structured JSON output)
- Q4_K_M is the recommended balance of speed vs quality
- If quality degradation is observed, try higher bitrates: `Q5_K_M`, `Q6_K`, `Q8_0`
- Temperature 0 + JSON mode ensures deterministic output

## Installation

```bash
# Standard CPU
pip install llama-cpp-python

# With OpenBLAS (faster on Intel/AMD)
CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" pip install llama-cpp-python

# Or from apps/aiEnrichNew
uv add llama-cpp-python
```

For Windows without MSVC build tools, use pre-built wheels:
```bash
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

## Rollback

- Revert `llm_client.py` and `llm_utils.py` to previous versions
- Restore `transformers` + `torch` in `pyproject.toml`
- Delete the downloaded GGUF file from Hugging Face cache

## Implementation Order

1. Install `llama-cpp-python` (may need build tools — test first)
2. Rewrite `llm_client.py` with `Llama` class
3. Adjust `llm_utils.py` for the new API
4. Update `pyproject.toml` dependencies
5. Run `uv sync` + test with a sample job
6. Compare results quality vs current aiEnrich (Ollama) output

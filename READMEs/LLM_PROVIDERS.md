# LLM providers

The three AI workers (`aienrich`, `aienrichskill`, `aiFormFiller`) share one OpenAI-compatible client in [`commonlib/cloud_llm.py`](../apps/commonlib/commonlib/cloud_llm.py). Local engines stay the default; cloud providers are opt-in and can be switched live in **Settings → LLM Providers** (changes apply on the next worker cycle).

Put every key in `.env.secrets` (template: [`scripts/.env.secrets.example`](../scripts/.env.secrets.example)), never in `.env`. Settings can also write them directly. Free-tier quotas and model availability change frequently — use the official links below as the source of truth.

| Provider | Selector value | Base URL | Key | Default model |
|---|---|---|---|---|
| OpenRouter | `openrouter` | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` | `openrouter/free` (fallback `nex-agi/nex-n2.5-pro:free`) |
| Google Gemini | `gemini` | `https://generativelanguage.googleapis.com/v1beta/openai` | `GEMINI_API_KEY` | `gemini-2.5-flash-lite` |
| Groq | `groq` | `https://api.groq.com/openai/v1` | `GROQ_API_KEY` | `openai/gpt-oss-20b` |
| Cerebras | `cerebras` | `https://api.cerebras.ai/v1` | `CEREBRAS_API_KEY` | `llama-3.3-70b` |
| HuggingFace Inference | `hf-inference` | `https://router.huggingface.co/v1` | `HF_TOKEN` | `Qwen/Qwen2.5-1.5B-Instruct` |

Local values are `ollama` (aiEnrich/aiEnrichSkill), `huggingface` (aiEnrichSkill) and `local` (aiFormFiller). These do not need a cloud key.

## Official limits and model lists

- [OpenRouter free models](https://openrouter.ai/models?max_price=0) — free model slugs often end in `:free`; the `openrouter/free` router picks one automatically.
- [Gemini API rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) — limits are per project and reset daily; [model list](https://ai.google.dev/gemini-api/docs/models).
- [Groq rate limits](https://console.groq.com/docs/rate-limits) — free tier is per organization; [model list](https://console.groq.com/docs/models).
- [Cerebras models and rate limits](https://inference-docs.cerebras.ai/).
- [HuggingFace Inference Providers](https://huggingface.co/docs/inference-providers/index) — free credits are account-limited.

## Model overrides

Each provider supports an optional `<PROVIDER>_MODEL` and `<PROVIDER>_BASE_URL` in `.env` (for example `GEMINI_MODEL`, `GROQ_MODEL`, `CEREBRAS_MODEL`, `HF_INFERENCE_MODEL`, `OPENROUTER_MODEL`). The worker reads them on every cycle, so Settings edits apply without a restart. aiEnrich additionally honors `AI_ENRICH_OPENROUTER_MODEL`, `AI_ENRICH_OPENROUTER_BASE_URL` and `AI_ENRICH_OPENROUTER_FALLBACK_MODEL`.

Keep a fallback model for JSON-producing jobs (aiEnrich): free routers rotate models, and a model that ignores `response_format` makes the job fail validation. OpenRouter has a configured fallback; other providers simply retry with the same model, so pick a model with structured-output support when possible.

## Not integrated

Cloudflare Workers AI also has a free allowance, but its URL contains an account ID rather than only a key, so it is documented here instead of appearing in the selectors. Use a compatible gateway such as OpenRouter if you need it through this client.

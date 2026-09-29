# AI Form Filler

AI-powered tool that answers job application form questions using your CV and preferences. Consists of a **FastAPI backend** and a **browser extension** (Chrome + Firefox).

## How It Works

```
1. Right-click a form field → "Answer with AI"
2. Side panel opens with detected question
3. Backend reads your CV + looking-for document
4. AI generates an honest answer (or asks for clarification if info is missing)
5. Click "Rellenar campo" to auto-fill the field
```

## Architecture

```
Browser Extension (side panel) ←→ FastAPI Backend (localhost:8080) ←→ AI Provider
                                                                      ├── Local HF (Qwen2.5)
                                                                      ├── OpenAI (GPT-4o mini)
                                                                      └── OpenRouter (multiple models)
```

## Setup

### 1. Prepare context documents

Edit `cv/cv.txt` with your CV text:

```
5 years of experience in Java, Spring Boot...
```

Edit `cv/looking-for.txt` with your preferences:

```
# What I'm looking for
- Desired role: Senior Software Engineer
- Desired salary: 70.000€ - 85.000€
- Contract type: Indefinite / Freelance
- Location: Remote (Spain)
- Preferred technologies: Java, Spring Boot, Kotlin
- Availability: Immediate
```

### 2. Start the backend

```bash
cd apps/aiFormFiller
uv run uvicorn aiFormFiller.main:app --host 127.0.0.1 --port 8080
```

Or use the run script:

```bash
# Windows
.\apps\aiFormFiller\run.bat

# Linux/macOS
./apps/aiFormFiller/run.sh
```

### Docker

The service starts by default with `docker-compose up -d`.

The backend starts on `http://127.0.0.1:8080`. API docs at `/docs`.

### 3. Install the browser extension

**Chrome:**
1. Go to `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked" → select `apps/aiFormFiller/extension/`

**Firefox:**
1. Go to `about:debugging#/runtime/this-firefox`
2. Click "Load Temporary Add-on"
3. Select `apps/aiFormFiller/extension/manifest.json`

## Usage

1. Navigate to any job application form
2. Click on a text field (input or textarea)
3. Right-click → **"Answer with AI"**
4. The side panel opens with the detected question
5. Click **"Responder"** to get an AI-generated answer
6. If the AI needs more info, a clarification box appears — type the missing info and click **"Enviar y responder"**
7. Click **"Rellenar campo"** to fill the original form field, or **"Copiar"** to copy manually

## AI Providers

Configure via `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_FORM_PROVIDER` | `local` | `local`, `openai`, `openrouter`, or `auto` |
| `AI_FORM_HF_MODEL` | `Qwen/Qwen2.5-1.5B-Instruct` | Local HuggingFace model |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model name |
| `OPENROUTER_API_KEY` | — | OpenRouter API key |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` | OpenRouter model (e.g. `anthropic/claude-3-haiku`) |
| `AI_FORM_PORT` | `8080` | Backend port |
| `AI_FORM_TIMEOUT` | `30` | API timeout in seconds |
| `AI_FORM_TEMPERATURE` | `0.1` | LLM temperature (lower = more deterministic) |
| `AI_FORM_MAX_TOKENS` | `512` | Max response tokens |
| `AI_FORM_CV_PATH` | `cv/cv.txt` | Path to CV document |
| `AI_FORM_LOOKING_FOR_PATH` | `cv/looking-for.txt` | Path to preferences document |

### Provider selection logic

- `local` — Uses HuggingFace transformers with the model from `AI_FORM_HF_MODEL`. Works offline, no API key needed.
- `openai` — Uses OpenAI API. Requires `OPENAI_API_KEY`.
- `openrouter` — Uses OpenRouter API. Requires `OPENROUTER_API_KEY`. Supports many models (Claude, Gemini, GPT, etc.).
- `auto` — Tries local first, falls back to configured provider.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check + provider/context status |
| `POST` | `/api/answer` | Ask a question, get an answer or clarification |
| `POST` | `/api/answer/follow-up` | Provide additional info after a clarification |

### POST /api/answer

```json
// Request
{ "question": "¿Cuántos años de Java tienes?", "provider": "auto" }

// Response (direct answer)
{ "type": "answer", "text": "Tengo 5 años de experiencia con Java...", "provider": "local", "confidence": "high" }

// Response (clarification needed)
{ "type": "clarification", "text": "CLARIFICACIÓN: Tu CV no menciona Spring Boot 3.x...", "provider": "local", "confidence": "low" }
```

### POST /api/answer/follow-up

```json
// Request
{ "original_question": "¿Cuántos años de Spring Boot 3?", "clarification_answer": "Sí, desde 2023" }

// Response
{ "type": "answer", "text": "Tengo 2 años de experiencia con Spring Boot 3.x...", "provider": "local", "confidence": "high" }
```

## Structured logging

Telemetry goes through `commonlib.observability` instead of `print()`. Because `main.py` builds the app at module level (`app = create_app()`), `configure_logging("aiFormFiller")` runs at module level right after the imports, so the import-time events from `create_app()` land in `aiFormFiller.jsonl` too; every module then binds a logger at module level:

```python
logger = get_logger("aiFormFiller.routes")
logger.exception("provider.failed", endpoint="answer", provider=req.provider)
```

Console output goes to stdout and every record is mirrored to a JSONL file, one JSON object per line, at `data/logs/aiFormFiller.jsonl` relative to the working directory - `apps/aiFormFiller/data/logs/aiFormFiller.jsonl` on the host, since the container mounts the app directory.

| Module | Events |
|---|---|
| `main` | `app.created` (info); `app.context_loaded` (info, booleans for the CV and looking-for documents); `app.started` (info, version, host and port) |
| `api/routes` | `form.answered` (debug, one per request, with the endpoint, provider, clarification flag and the question/answer lengths); `provider.rejected` (warning, a `ValueError` such as a missing API key, becomes HTTP 400); `provider.failed` (exception - records the traceback, becomes HTTP 500) |
| `context_loader` | `context.cv_loaded`, `context.looking_for_loaded` (info); `context.cv_reloaded`, `context.looking_for_reloaded` (info, the documents are re-read on every request when their mtime changes); `context.file_not_found`, `context.file_empty` (warning) |
| `models/local_hf` | `model.loading`, `model.loaded` (info, provider and model id; the pipeline is built once and cached) |

Conventions: event names are dotted `domain.action` and never free text; dynamic values are `key=value` fields and no f-string is ever passed to a log call; `debug` is per-request detail, `info` is lifecycle, `warning` is recoverable, `exception` is a failed provider call with its traceback. The service handles the CV and the LLM conversation, so **nothing from the documents, the prompts, the questions or the model answers is ever logged** - only lengths, counts, flags, provider names and paths. The HTTPException raised from the failure branches is unchanged; the `provider.failed` record is what makes those failures visible, because the 500 response body alone does not say which provider broke. No `print()` remains in this app.

### Configuration

| Variable | Default | Description |
|---|---|---|
| `LOG_LEVEL` | `20` | 10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR |
| `LOG_COLOR` | `True` | Colored console output instead of raw JSON on stdout |
| `LOG_DIR` | `data/logs` | Directory holding `aiFormFiller.jsonl` |
| `LOG_FILE_MAX_BYTES` | `10485760` | Rotate the JSONL file once it grows past this |
| `LOG_FILE_BACKUP_COUNT` | `5` | Rotated files to keep |

Set `LOG_LEVEL=10` to get the per-request `form.answered` records. These variables are shared with every other app; see [Structured Logging](../../READMEs/README_DEVELOPMENT.md#structured-logging) for the full reference.

## Development

```bash
cd apps/aiFormFiller

# Install dependencies
uv sync

# Run tests
uv run pytest

# Run with coverage
uv run coverage run -m pytest && uv run coverage report -m
```

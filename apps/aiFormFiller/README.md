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

From the repository root:

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

Run the installer from the repository root. It packs the extension into a signed CRX (Chrome) and an XPI (Firefox) and registers it for all existing profiles, so a browser restart is all that is needed:

```bash
# Windows
.\apps\aiFormFiller\install-extension.bat

# Linux/macOS
./apps/aiFormFiller/install-extension.sh
```

Use `--browser chrome|firefox` to install only one browser, and `--dry-run` to preview the changes. The generated packages and signing key live in `~/.ai-form-filler` (`%LOCALAPPDATA%\ai-form-filler` on Windows); keep them so reinstalls keep the same extension ID.

| Browser | Platform | Mechanism | Rights |
|---|---|---|---|
| Chrome | Linux | [External extensions](https://developer.chrome.com/extensions/external_extensions) (user-removable) | `sudo` |
| Chrome | Windows/macOS | `ExtensionInstallForcelist` policy (must be removed with the uninstall script) | admin / `sudo` |
| Firefox | all | `policies.json` → `Extensions.Install` | admin / `sudo` |

To remove the registration and the generated packages:

```bash
# Windows
.\apps\aiFormFiller\uninstall-extension.bat

# Linux/macOS
./apps/aiFormFiller/uninstall-extension.sh
```

Manual development install is still available: load `apps/aiFormFiller/extension/` unpacked in Chrome under `chrome://extensions` with Developer mode enabled. The Firefox package built by the script adds the gecko manifest keys and a small API shim that the shared source manifest does not contain, so use the script for Firefox.

## Usage

1. Navigate to any job application form
2. Right-click a form field → **"Answer with AI"**
3. The side panel opens with the questions detected in that form
4. Choose a **Provider** if needed, then click **"Answer All"**
5. Click **"Fill All"** to write the answers back into the form

The panel is tab-specific: it opens only on tabs where you used "Answer with AI", hides when you switch to other tabs, and shows each form tab's own questions and answers when you return to it.

## AI Providers

Configure via `.env`:

The side panel **Provider** dropdown overrides the backend default for that browser profile; **Auto (backend)** follows `AI_FORM_PROVIDER`. The selection is stored locally in the browser and applies to answer, batch and follow-up requests.

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

For low-latency inference without a local model, set `AI_FORM_PROVIDER=openrouter` and `OPENROUTER_MODEL=<model>:free` (e.g. `nvidia/nemotron-3.5-lightning:free`); reasoning is disabled automatically for `:free` models so the response is a plain answer. Free providers may rate-limit requests.

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

The service handles the CV and the LLM conversation, so **nothing from the documents, the prompts, the questions or the model answers is ever logged** - only lengths, counts, flags, provider names and paths. The `provider.failed` record is what makes provider failures visible, because the 500 response body alone does not say which provider broke. Event names, levels, and the shared `LOG_*` variables are documented in [Structured Logging](../../READMEs/README_DEVELOPMENT.md#structured-logging); set `LOG_LEVEL=10` for the per-request `form.answered` records.

## Development

Dependencies are installed from the repository root with `./scripts/install.sh` (Linux/Mac) or `.\scripts\install.bat` (Windows).

```bash
# From the repo root: tests through the centralized runner
./scripts/test.sh commonlib aiFormFiller   # Linux/Mac
.\scripts\test.bat commonlib aiFormFiller  # Windows

# With coverage
./scripts/test.sh --coverage commonlib aiFormFiller
```

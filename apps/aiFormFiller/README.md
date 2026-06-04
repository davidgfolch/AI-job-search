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

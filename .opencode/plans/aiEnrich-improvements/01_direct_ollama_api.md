# Plan A: Direct Ollama API (Remove CrewAI)

## Goal

Replace CrewAI orchestration with direct HTTP calls to Ollama's API, eliminating ~1-3s of overhead per job.

## Rationale

The current `DataExtractor` wraps a **single agent + single task** in a sequential CrewAI process:

```python
@CrewBase
class DataExtractor:
    @agent
    def extractor_agent(self) -> Agent: ...
    @task
    def extractor_task(self) -> Task: ...
    @crew
    def crew(self) -> Crew: ...
```

This adds CrewAI's internal machinery (agent parsing, task delegation, callback hooks, output formatting) with zero benefit for a single-agent-single-task workflow. The actual work is: build prompt → send to Ollama → parse JSON response.

## Architecture

```
Before:     DB → AiEnrichRepository → DataExtractor.crew() → CrewAI orchestration → Ollama HTTP → CrewOutput → parse → DB
After:      DB → AiEnrichRepository → build_prompt() → requests.post(Ollama) → parse JSON → DB
```

## Files to Create

### `apps/aiEnrich/src/aiEnrich/ollama_client.py`

Thin wrapper around Ollama's generate API:

```python
def query_ollama(
    prompt: str,
    model: str = "ollama/qwen2.5:3b",
    base_url: str = "http://localhost:11434",
    timeout: int = 90,
    json_mode: bool = True,
) -> dict | None
```

- Uses `requests.post(f"{base_url}/api/generate", json={...})`
- Supports `stream=False` for simplicity
- Passes `options={"temperature": 0, "num_predict": 256}` 
- Supports `format="json"` for structured output
- Error handling: 2 retries with exponential backoff (1s, 3s)
- Logs warnings on failure, returns None

## Files to Modify

### `apps/aiEnrich/src/aiEnrich/dataExtractor.py`

- Remove `@CrewBase`, `DataExtractor` class, all `agent`/`task`/`crew` decorators
- Replace `crew = DataExtractor().crew()` → call `query_ollama()` directly
- Build prompt inline from the template in `tasks.yaml` + job markdown
- Remove `combineTaskResults()` (no multi-task CrewOutput to process)
- Parse JSON response with `rawToJson()` from `commonlib.json_helpers`
- Keep `_save()`, `_handle_error()`, `_process_job_safe()` logic unchanged

### `apps/aiEnrich/src/aiEnrich/crew.py`

- Remove `from crewai.flow.flow import Flow, start`
- Simplify `AiJobSearchFlow` to a plain class or module-level loop
- No longer need the `@start()` decorator

### `apps/aiEnrich/src/aiEnrich/skillEnricher.py`

- Same pattern: replace `Agent` + `Task` + `Crew` with direct `query_ollama()`
- Build the skill description prompt directly as a string
- Keep the business logic (`parse_skill_llm_output`, DB interactions)

### `apps/aiEnrich/pyproject.toml`

```diff
- crewai[tools]>=0.80.0,<1.0.0
+ requests>=2.31.0
```

## Dependencies

- `requests` (likely already present transitively, add explicitly)

## Quality Considerations

- Same model (`ollama/qwen2.5:3b`) → same extraction quality
- Same prompt template (from `tasks.yaml`) → same input
- JSON mode (`format="json"`) reduces malformed responses
- Temperature stays at 0 → deterministic output

## Rollback

- Revert changes to `dataExtractor.py`, `crew.py`, `skillEnricher.py`
- Restore `crewai[tools]` in `pyproject.toml`
- Delete `ollama_client.py`

## Implementation Order

1. Create `ollama_client.py`
2. Rewrite `dataExtractor.py` — remove CrewBase, use direct API
3. Simplify `crew.py` — remove Flow
4. Rewrite `skillEnricher.py` — same pattern
5. Update `pyproject.toml` — swap dependencies
6. Run `uv sync` + existing tests

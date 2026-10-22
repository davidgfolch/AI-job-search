# TODO

## try claude with ollama run qwen3-coder-next

Didn't install required ollama pre-resease.

[ollama linkedin post](https://www.linkedin.com/posts/ollama_ollama-run-qwen3-coder-next-qwen3-coder-next-activity-7424756919287902208-qDd0?utm_source=share&utm_medium=member_desktop&rcm=ACoAAAZZizwBuntXrHiItXZY-quYzSMB_DQy5oM)

```bash
ollama run qwen3-coder-next
ollama launch claude --config 
# docker sandbox run claude ~/projects/AI-job-search/
```

## try claude with ommana 
[claude ollama](https://www.linkedin.com/posts/uttammgupta-aisolutionsexpert_claude-code-ai-share-7424786356650045440-kxRX?utm_source=share&utm_medium=member_desktop&rcm=ACoAAAZZizwBuntXrHiItXZY-quYzSMB_DQy5oM)

## cross module tasks

- move scrapper debug to commonlib
- find death code (vibe coding) 
  - scrapper done
  - backend done
  - all apps covered by the enforced static-analysis gate (ruff `F401`/`F841`/`F811`/`ARG` + the full bugbear set, eslint + `tsc -b`); see [Static Analysis](README_DEVELOPMENT.md#static-analysis)
- Filter Configurations Storage: done (MySQL `filter_configurations` + backend API + statistics endpoint; frontend uses the backend with localStorage fallback and migration).

## apps/aiEnrich

- aiEnrich* common implementation abstractions to commonlib: done (shared `strip_code_fence` in `commonlib/json_helpers`, aiEnrich now uses the shared Ollama probe cache via `commonlib.ollama_probe`)

## apps/backend

## apps/commonlib

## apps/scrapper

- move scrapper debug to commonlib: done (`commonlib/debug_utils.debug`, scrapper re-exports it)

## apps/web
- In list, when selected all, it don't un select when click on selected row.  It unselects all, and select the row. The problem is even bigger because is an api bulk operation LLM decided to pass all form filters, so if you change a filter (eg. ignored) the bulk reques doesn't work.: done (clicking a row in "all" mode deselects only it and switches to manual with the rest; bulk mutations refetch the active job queries)
- "Clean - Ignore jobs by title" dont update job list when all ignored & there is pagination scrolled down.: done (auto-selects all when the clean config is active and page > 1, and bulk updates refetch the list so ignored jobs disappear)

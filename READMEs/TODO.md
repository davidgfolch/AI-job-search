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
- Filter Configurations Storage: Filter configurations are currently stored in browser localStorage (frontend-only). This implementation will work by sending filter configurations from the frontend to the backend for job counting. The configurations themselves will not be persisted in the backend database. Update apps/web, backend & statistics.

## apps/aiEnrich

- aiEnrich* common implementation abstractions to commonlib

## apps/aiEnrichNew

- improvements:
  - Detect: "Sueldo bruto / año en 30.000b/a - 38.000b/a"
  - Detect: relocation, on-site, híbrido or hybrid obligation to go to office (and set comments or change tables by adding a new field)
- aiEnrich* common implementation abstractions to commonlib

## apps/backend

## apps/commonlib

## apps/scrapper

## apps/web
- in apps/web, solve duplicated ids for edit/create fields: client, comments & salary
- In list, when selected all, it don't un select when click on selected row.  It unselects all, and select the row. The problem is even bigger because is an api bulk operation LLM decided to pass all form filters, so if you change a filter (eg. ignored) the bulk reques doesn't work.
- "Clean - Ignore jobs by title" dont update job list when all ignored & there is pagination scrolled down.

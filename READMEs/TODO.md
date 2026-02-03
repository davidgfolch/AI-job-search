# TODO

## cross module tasks

- move scrapper debug to commonlib
- find death code (vibe coding) 
  - scrapper done
  - backend done
- Filter Configurations Storage: Filter configurations are currently stored in browser localStorage (frontend-only). This implementation will work by sending filter configurations from the frontend to the backend for job counting. The configurations themselves will not be persisted in the backend database. Update apps/web, backend & statistics.

## apps/aiEnrich

- aiEnrich* common implementation abstractions to commonlib

## apps/aiEnrichNew

- aiEnrich* common implementation abstractions to commonlib

## apps/backend

## apps/commonlib

## apps/scrapper

## apps/web
- in apps/web, solve duplicated ids for edit/create fields: client, comments & salary
- In list, when selected all, it don't un select when click on selected row.  It unselects all, and select the row. The problem is even bigger because is an api bulk operation LLM decided to pass all form filters, so if you change a filter (eg. ignored) the bulk reques doesn't work.
- "Clean - Ignore jobs by title" dont update job list when all ignored & there is pagination scrolled down.

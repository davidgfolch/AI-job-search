# TODO

## cross module tasks

- move scrapper debug to commonlib
- find death code (vibe coding) 
  - scrapper done
  - backend done
- fix time in mysql created date column 1 hour less


## apps/aiEnrich

- aiEnrichError retry when all others are done

## apps/aiEnrichNew

- aiEnrichError retry when all others are done

## apps/backend

## apps/commonlib

## apps/scrapper
- linked in didn't parse markdown correctly in this [job](http://localhost:5173/?jobId=464423&order=created+desc&days_old=1&salary=%5Cd%2B&flagged=null&like=null&ignored=false&seen=false&applied=false&discarded=false&closed=false&interview_rh=null&interview=null&interview_tech=null&interview_technical_test=null&interview_technical_test_done=null&ai_enriched=true&easy_apply=null)
- reruning errored scrappers after 30 minutes goes to cloudflare filter all the time, rerun in 30 minutes should be configurable for each scrapper.

## apps/web
- in apps/web, solve duplicated ids for edit/create fields: client, comments & salary
- In list, when selected all, it don't un select when click on selected row.  It unselects all, and select the row. The problem is even bigger because is an api bulk operation LLM decided to pass all form filters, so if you change a filter (eg. ignored) the bulk reques doesn't work.
- "Clean - Ignore jobs by title" dont update job list when all ignored & there is pagination scrolled down.

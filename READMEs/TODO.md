# TODO

## cross module tasks

- find death code (vibe coding)


## apps/aiEnrich

- aiEnrichError retry when all others are done

## apps/aiEnrichNew

- aiEnrichError retry when all others are done

## apps/backend

## apps/commonlib

## apps/scrapper
- DONE: summary: show state of each scrapper
- DONE: indeed: Starting page X of X.XXXX -> total pages shows decimals.
- DONE: indeed FIX cloudflare filter with undetected-chromedriver, when load & when enter email OTP password too!!!
- DONE: infojobs FIX cloudflare filter with undetected-chromedriver
- reruning errored scrappers after 30 minutes goes to cloudflare filter all the time, rerun in 30 minutes should be configurable for each scrapper.

## apps/web
- in apps/web, solve duplicated ids for edit/create fields: client, comments & salary
- In list, when selected all, it don't un select when click on selected row.  It unselects all, and select the row. The problem is even bigger because is an api bulk operation LLM decided to pass all form filters, so if you change a filter (eg. ignored) the bulk reques doesn't work.
- "Clean - Ignore jobs by title" dont update job list when all ignored & there is pagination scrolled down.

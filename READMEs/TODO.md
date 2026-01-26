# TODO

## cross module tasks

- move scrapper debug to commonlib
- find death code (vibe coding) 
  - scrapper done
  - backend done


## apps/aiEnrich

- aiEnrichError retry when all others are done

## apps/aiEnrichNew

- aiEnrichError retry when all others are done

## apps/backend

## apps/commonlib

## apps/scrapper
- indeed: didn't load the page:

      Indeed DEBUG: False
      Preventing Windows system sleep...
      ------------------------------------------------------------------------------------------------------------------------------------------------------
      2026-01-26 15:14:46 - RUNNING INDEED scrapper
      ------------------------------------------------------------------------------------------------------------------------------------------------------
      Search keyword=java
      Searching for "java" in "España"

      Search keyword=python
      Searching for "python" in "España"

      Search keyword=scala
      Searching for "scala" in "España"

      Search keyword=clojure
      Searching for "clojure" in "España"

      Search keyword=senior software engineer
      Searching for "senior software engineer" in "España"

      Scrapper finished with failed keywords. State preserved for retry.
      Allowing Windows system sleep...

- linked in didn't parse markdown correctly in this [job](http://localhost:5173/?jobId=464423&order=created+desc&days_old=1&salary=%5Cd%2B&flagged=null&like=null&ignored=false&seen=false&applied=false&discarded=false&closed=false&interview_rh=null&interview=null&interview_tech=null&interview_technical_test=null&interview_technical_test_done=null&ai_enriched=true&easy_apply=null)
- reruning errored scrappers after 30 minutes goes to cloudflare filter all the time, rerun in 30 minutes should be configurable for each scrapper.

## apps/web
- in apps/web, solve duplicated ids for edit/create fields: client, comments & salary
- In list, when selected all, it don't un select when click on selected row.  It unselects all, and select the row. The problem is even bigger because is an api bulk operation LLM decided to pass all form filters, so if you change a filter (eg. ignored) the bulk reques doesn't work.
- "Clean - Ignore jobs by title" dont update job list when all ignored & there is pagination scrolled down.

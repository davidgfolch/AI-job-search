# TODO

## cross module tasks

- find death code (vibe coding)


## apps/aiEnrich

## apps/aiEnrichNew

## apps/autofill
This is a prototype beta version, not working yet.

## apps/backend

## apps/commonlib

## apps/scrapper
- FIX cloudflare filter with undetected-chromedriver, when load & when enter email OTP password too!!!
- Indeed zero search results not showing info:

        Search keyword=scala
        Searching for "scala" in "España"
        Search keyword=clojure
        Searching for "clojure" in "España"
        Search keyword=senior software engineer
        Searching for "senior software engineer" in "España"

- Infojobs:

        2026-01-20 09:45:50- INFOJOBS Starting page 3 of 3 search=python
        ------------------------------------------------------------------------------------------------------------------------------------------------------
        pg 3 job 1 - Job id=i1017bf930e490986a1f4a0b3cb6fc1 already exists in DB, IGNORED.
        pg 3 job 2 - Job id=i7f520eb77343a59e2a3606fad52c72 already exists in DB, IGNORED.
        pg 3 job 3 -
        Traceback (most recent call last):
        File "C:\Users\TRENDINGPC\projects\AI-job-search\apps\scrapper\scrapper\executor\InfojobsExecutor.py", line 68, in _load_and_process_row
        url = self.navigator.get_job_url(job_link_elm)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        File "C:\Users\TRENDINGPC\projects\AI-job-search\apps\scrapper\scrapper\navigator\infojobsNavigator.py", line 123, in get_job_url
        return element.get_attribute('href')
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        File "C:\Users\TRENDINGPC\projects\AI-job-search\apps\scrapper\.venv\Lib\site-packages\selenium\webdriver\remote\webelement.py", line 231, in get_attribute
        attribute_value = self.parent.execute_script(
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^
        File "C:\Users\TRENDINGPC\projects\AI-job-search\apps\scrapper\.venv\Lib\site-packages\selenium\webdriver\remote\webdriver.py", line 555, in execute_script
        return self.execute(command, {"script": script, "args": converted_args})["value"]
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        File "C:\Users\TRENDINGPC\projects\AI-job-search\apps\scrapper\.venv\Lib\site-packages\selenium\webdriver\remote\webdriver.py", line 458, in execute
        self.error_handler.check_response(response)
        File "C:\Users\TRENDINGPC\projects\AI-job-search\apps\scrapper\.venv\Lib\site-packages\selenium\webdriver\remote\errorhandler.py", line 233, in check_response
        raise exception_class(message, screen, stacktrace)
        selenium.common.exceptions.StaleElementReferenceException: Message: stale element reference: stale element not found in the current frame
        (Session info: chrome=143.0.7499.193); For documentation on this error, please visit: https://www.selenium.dev/documentation/webdriver/troubleshooting/errors#staleelementreferenceexception

## apps/web
- In list, when selected all, it don't un select when click on selected row.  It unselects all, and select the row. The problem is even bigger because is an api bulk operation LLM decided to pass all form filters, so if you change a filter (eg. ignored) the bulk reques doesn't work.
- in "AI Job Search Statistics" add "by day of week" chart.

# Scrapers

The automatic scrapper `./run_2_Scrapper.sh` (without parameters) keeps running in a infinite loop in console:

> Different intervals have been set in `scrapper.py` for the execution times of each scraper, taking into account the volume of listings, the Anti Robot Security Filters (**ARSF**) & **RATE LIMITS** of each website.

- **Infojobs**: works fine, but it will show **ARSF** at the beginning of scrape.
- **LinkedIn**: works fine.
- **Glassdoor**: could show **ARSF** "all the time", scrapper just re-run selenium browser on error.
- **Tecnoempleo**: works fine.
- ~~**Indeed** **ARSF** all the time (DISABLED)~~

## ASRF & rate limits

To minimize Anti Robot Security Filters (**ASRF**), Selenium operations on each website are implemented with waits & mouse moves to mimic human behavior, but still **ASRF** could appear sometimes (or always as in Infojobs).  You can try an VPN to bypass **ASRF** Cloudflare.  Be aware that your fixed IP could be banned by Cloudflare **ASRF** if you exceed rate limits.

Also a @retry mechanism is implemented for random fails (page load's timeouts, etc).

To avoid **RATE LIMITS** security filters, job search's are limited to last 24 hours only, so scrappers must run at least each day to not miss job offers.  The automatic scrapper script `./run_2_Scrapper.sh`, control the times each web-site scrapping is executed to avoid security filters.

## Merge duplicated jobs

Duplicated jobs will be created in database when the origin web-site `jobId` is different for the same real job. So an automatic `mergeDuplicates.py` script is called after each insert in database.  It finds duplicated jobs by title-company & merges old jobs information into the newest one, copying states, ai-enriched fields & comments into the last one & deleting older ones.

## Implementations

### Infojobs

**ASRF** will appear on first page load, you'll need to solve it manually.

> That's why is the first one to execute in `./run_2_Scrapper.sh`, to after solved you can leave it working.

First time run is failing in the last days I've tried.

### Linkedin

Linkedin scraper works fine, but when I was developing the scrapper found several problems because I did too much requests:

- Rate limits: LinkedIn has rate limit even for authenticated users, so if you execute **`scrapper/linkedin.py`** several times or have too much `JOBS_SEARCH` keywords you will be spending LinkedIn rate limit.  If rate limit is exhausted all request will return a HTTP STATUS CODE = 429
- After some days executing the selenium script we also found a security human check, so we have to pause execution after login and solve puzzle manually.

### Glassdoor

**ASRF** will appear usually, randomly & page hangs eventually.  Auto-scrapper re-inits selenium driver when it fails.

## Specific scrapper paramters

There are other parameters you can change in **`scrapper/*.py`**

### Linkedin example

```python
remote = '2'   # ["2"],  # onsite "1", remote "2", hybrid "3"
# Spain if you need other make a manual search and get your country code
location = '105646813'
f_TPR = 'r86400'  # last 24 hours
# Set to True to stop selenium driver navigating if any error occurs
DEBUG = False
```

> NOTE: changing those could cause violation of LinkedIn rate limit

### Glassdoor example

Glassdoor has an strange constructing the url with filters to show the list results, see `GLASSDOOR_JOBS_SEARCH`
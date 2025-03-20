# Scrapers

The automatic scrapper (`./run_2_Scrapper.sh` without parameters) keeps running in a infinite loop in console.  Different timeouts are configured in `scrapper.py` for each site scrapper.

To avoid RATE LIMITS security filters, job search's are limited to last 24 hours only (sorting newest first), so scrappers must run at least each day to not miss job offers.  The automatic scrapper script `./run_2_Scrapper.sh`, control the times each web-site scrapping is executed to avoid security filters.

| KNOWN PROBLEMS | Solution |
|--------|-------|
| Scrappers can fail randomly | Re-run |
| Scrappers could fail due to (random) anti-robot security filters or any other reason| Set `DEBUG=True` in the failing scrapper, re-run & solve security filter |

## Merge duplicated jobs

Duplicated jobs will be created in database when the origin web-site `jobId` is different for the same real job. So an automatic `mergeDuplicates.py` script is called after each insert in database.  It finds duplicated jobs by title-company & merges old jobs information into the newest one, copying states, ai-enriched fields & comments into the last one & deleting older ones.

## Implementations

### Infojobs

Security filter will appear, you'll need to solve it manually & press a key in the terminal

### Linkedin

Rate limits: LinkedIn has rate limit even for authenticated users, so if you execute **`scrapper/linkedin.py`** several times or have too much `JOBS_SEARCH` keywords you will be spending LinkedIn rate limit.  If rate limit is exhausted all request will return a HTTP STATUS CODE = 429

After some days executing the selenium script we also found a security human check, so we have to pause execution after login and solve puzzle manually.

![alt text](img/LinkedInSecurityVerification.png)

### Glassdoor

Security filter may appear, page hangs eventually.  Auto-scrapper re-inits selenium driver when it fails.

### Other parameters

There are other parameters you can change in **`scrapper/*.py`**

For example for Linkedin:

```python
remote = '2'   # ["2"],  # onsite "1", remote "2", hybrid "3"
# Spain if you need other make a manual search and get your country code
location = '105646813'
f_TPR = 'r86400'  # last 24 hours
# Set to True to stop selenium driver navigating if any error occurs
DEBUG = False
```

> NOTE: changing those could cause violation of LinkedIn rate limit

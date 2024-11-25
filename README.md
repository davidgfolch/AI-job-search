# AI Job Search

This is a helper to search & find jobs on LinkedIn.

Using selenium to get data storing job offers in a database.
Using artificial intelligence to enrich the database with structured information.

## LinkedIn scraper

Rate limits: LinkedIn has rate limit even for authenticated users, so if you execute **`seleniumLinkedin.py`** several times or have too much `JOBS_SEARCH` keywords you will be spending LinkedIn rate limit.  If rate limit is exhausted all request will return a HTTP STATUS CODE = 429

After some days executing the selenium script we also found a security human check, so we have to pause execution after login and solve puzzle manually.

![alt text](README-images/LinkedInSecurityVerification.png)

### Setup LinkedIn scraper

Setup credentials & search concepts in `.env` file:

#### Credentials

```python
# LinkedIn credentials
USER_EMAIL=yourmail@domain.com
USER_PWD=yourSecretLinkedInPass
# LinkedIn credentials
JOBS_SEARCH=java,python,scala,clojure,senior software engineer
```

#### Other parameters

There are other parameters you can change in **`seleniumLinkedin.py`**

```python
remote = '2'   # ["2"],  # onsite "1", remote "2", hybrid "3"
# Spain if you need other make a manual search and get your country code
location = '105646813'
f_TPR = 'r86400'  # last 24 hours
# Set to True to stop selenium driver navigating if any error occurs
DEBUG = False
```

> NOTE: changing those could cause violation of LinkedIn rate limit

### Search concepts

Modify search contents in `run()` method, default:

```python
searchJobs('senior software engineer')
searchJobs('java')
searchJobs('python')
searchJobs('scala')
searchJobs('clojure')
```

## Run sites scraper

```bash
./runSitesScraper.sh
```

## Run AI enricher (optional)

This will run LLM filling some extra fields from the job offer.

Using CrewAI framework (using local Ollama LLM by default).

```bash
./runAiEnricher.sh
```

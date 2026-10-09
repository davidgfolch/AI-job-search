# Fix scrapper job failures logged on 2026-10-09

Status: completed

## Problem

`apps/scrapper/data/logs/scrapper.jsonl` accumulated repeated errors for 2026-10-09 (UTC). Triaged into these items:

- **T1** — Tecnoempleo toast overlay (lipstick banner) intercepted clicks; jobs were retried forever or failed.
- **T2** — Tecnoempleo salary always empty: the new DOM renders an optional `Imprescindible Residir`/`Otras Provincias` row, so the fixed-position caption selector missed `Salario`.
- **T3** — Tecnoempleo company always empty after the rethink of the company link: `_read_link` relied on a `@retry` that masked the missing text node.
- **E5** — Indeed SERP links lost their pagead/no-jk ad entries; stored URLs were being normalized (`url varchar(300)`) so long query strings broke inserts.
- **I1** — Infojobs `scroll_jobs_list` retries on every job: verified as handled recovery noise, no fix needed.
- **E1** — LinkedIn stuck on `failed_keywords=["clojure"]`: the results-count header never rendered, `get_total_results` ran out of retries, the keyword was marked failed, and `should_skip_keyword` skipped it forever as "already processed".
- **E4** — Indeed offers whose detail page has no company profile (`e1ae8ce6fbd2a60c`, `88ffeb3aa1068e86`) scraped with an empty company (`job.field_invalid` every cycle), and broken links (`0f1e2d3c4b5a6978` and 4 more) rendered `No podemos encontrar esta página` with empty company+markdown.

## Solution

- **T1** (`tecnoempleoNavigator.py`): dismiss the toast overlay right after login; if a toast re-appears over a click (still intercepted), accept the click once without retrying and move on.
- **T2** (`tecnoempleoNavigator.py`): the salary reader matches the `Salario` caption in the "Datos principales" rows instead of a fixed row position; offers with no stated range store `salary=NULL`.
- **T3** (`tecnoempleoNavigator.py`): `TecnoempleoCompanyReader._read_link` reads the company link and falls back to the bare text node when the offer has no company page; the `@retry`-driven recursion was dropped.
- **E5** (`IndeedService.py`, `job_repository.py`): URL canonicalization for the stored url; pagead entries without a `jk` are skipped; the repository now logs the original exception on insert failure.
- **E1** (`linkedinNavigator.py`, `LinkedinExecutor.py`, `persistence_manager.py`): `get_total_results` is `@retry(... raiseException=False, retries=6, delay=3)` and returns `0` instead of raising when the header never renders; the executor logs `linkedin.total_results_unavailable` and skips the keyword cycle (not recorded as failed). `should_skip_keyword` never reports a previously-failed keyword as "already processed", so failed keywords are always retried on the next cadency while un-failed keywords before the resume point stay skipped.
- **E4** (`indeedScraplingNavigator.py`, `IndeedScraplingExecutor.py`): `CSS_SEL_COMPANY` tries `[data-testid='vj-company-name']` first (the RNW header node every offer renders) and then the company-page `a[href*="/cmp/"]` link, because offers without an Indeed company page expose no `/cmp/` link. `is_delisted()` detects HTTP 404 / `No podemos encontrar esta página` and `_load_and_process_row` skips those rows quietly (`indeed.scrapling.job.delisted_skipped`) — no validation errors, pagination keeps moving.
- **retry.py** (`commonlib`): `retry.exhausted` logs at **warning** with `exc_info=True` when `raise_exception=False`, and at error otherwise — the try-numbers at WARN/ERROR in the logs now mean different things.

The Indeed live-page analysis used the `crawlee-page-analyst` workflow: `PlaywrightCrawler` was Cloudflare-blocked (401/403), so the DOMs were fetched through the repo's own `ScraplingService` (`StealthySession`, `solve_cloudflare=True`, the exact vector the executor uses). All three target pages (two company-empty, one control) confirmed `vj-company-name` as the company node and the 404 + `h1` text as the delisted marker.

## Outcome

- Tecnoempleo toast, salary and company issues resolved; 2026-10-10+ logs show no repeats.
- LinkedIn recovered: `clojure` was retried (1 result found, deduped), all 6 keywords processed consecutively, the `scrapper_state.Linkedin` row was cleared, and missing-header runs log `linkedin.total_results_unavailable` + skip instead of failing.
- Indeed: `e1ae8ce6fbd2a60c` → `Sim Local (Ireland) Limited`, `88ffeb3aa1068e86` → `Squad Ciberseguridad` verified live through the real navigator; `0f1e2d3c4b5a6978` reports `delisted=True` (404) and is skipped. Control job (`a03ab3590d3f8240`, Cognizant) unchanged.
- Full suite: `./scripts/test.sh commonlib scrapper` → 755 passed.

Commits: batch fixes `65be7974`, LinkedIn fix `9384eac5`, this phase covers the E4 Indeed fix plus this plan and the scrapper README updates.
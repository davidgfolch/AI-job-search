---
name: crawlee-page-analyst
description: Use this skill to analyze a source page that changed (DOM/URL redesign) with Crawlee before changing apps/scrapper, producing selector-level requirements for the fix.
---

# Crawlee Page Analyst Instructions

https://crawlee.dev/python/docs/quick-start

Follow these steps when a scrapper broke because the source page changed its DOM structure, markup, or URL layout. Analyze the live page with Crawlee **before** editing any scrapper code, and turn the findings into requirements.

1.  **Confirm the Trigger**: Use this skill when a scrapper fails after a source-page change (selectors return nothing, fields are empty, the page redirects to a new URL pattern, or the site moved to a new frontend). Reproduce the failure first (run the scrapper once, check the structured logs) so the analysis targets a concrete symptom.

2.  **Environment Setup**:
    - Ensure the Crawlee CLI is installed: `uv tool install "crawlee[all]"` (done automatically by `scripts/install.sh` / `scripts/install.bat`).
    - Verify with `uv tool list | grep crawlee` or `crawlee --help`. Python 3.10+ required.
    - If `PlaywrightCrawler` fails on browser launch, run `playwright install chromium` once.
    - Crawlee runs outside the scrapper environment: use `uvx --with "crawlee[all]" python <script.py>` for ad-hoc analysis scripts so `apps/scrapper` dependencies stay untouched.

3.  **Analyze the Live Page**:
    - Fetch the changed URL with the crawler that matches the page: `PlaywrightCrawler` for JavaScript-rendered pages, `BeautifulSoupCrawler` or `ParselCrawler` for static HTML.
    - Dump the DOM of the affected page(s) and locate every selector the current scrapper uses (see `apps/scrapper/scrapper/navigator/` and `apps/scrapper/scrapper/services/`).
    - Classify each selector: still matches / matches different elements / no longer matches. Do the same for URL patterns, pagination links, and any `data-testid` or class-name contracts the scrapper relies on.
    - Minimal example for dumping and probing a page:
      ```python
      import asyncio
      from crawlee.crawlers import PlaywrightCrawler

      async def main() -> None:
          crawler = PlaywrightCrawler()

          @crawler.router.default_handler
          async def handler(context) -> None:
              html = await context.page.content()
              for selector in ['.old-title', '[data-testid="title"]']:
                  count = await context.page.locator(selector).count()
                  context.log.info(f'{selector}: {count} matches')
              await context.push_data({'url': context.request.url, 'html': html})

          await crawler.run(['https://example.com/jobs/123'])

      if __name__ == '__main__':
          asyncio.run(main())
      ```

4.  **Produce Requirements**: Report the analysis before implementing. The requirements must state:
    - Which fields (title, company, location, description, salary, flags) still extract correctly and which broke.
    - The new selectors/URL patterns to adopt, plus fallback selectors when the site is mid-migration (keep legacy selectors as fallback, as done for the Indeed viewjob rewrite).
    - Whether the change affects the Selenium path, the Scrapling path, or both, and whether a new feature flag or env var is needed.
    - Any anti-bot or rendering change (e.g. page moved to client-side rendering) that forces a different crawler class.

5.  **Implement & Test**:
    - Apply the agreed requirements in `apps/scrapper` following the existing architecture (navigator/service split, feature flags, `.env` config).
    - Keep implementations isolated per fetching technology (Selenium vs Scrapling vs Crawlee); do not share execution paths that assume a specific driver.
    - Update or add parameterized unit tests with mocked HTTP/browser responses (no live servers in CI) and run them via the centralized script: `./scripts/test.sh commonlib scrapper` (Linux/Mac) or `.\scripts\test.bat commonlib scrapper` (Windows).
    - Update `apps/scrapper/README.md` if selectors, fallbacks, or flags changed.

## Usage
Use this skill when the user reports that "the site changed", "the scraper broke after a redesign", "selectors stopped matching", or asks to "analyze the page changes before fixing the scrapper".

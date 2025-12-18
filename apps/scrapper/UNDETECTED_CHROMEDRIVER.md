# Undetected ChromeDriver Usage

## Overview

The scrapper now supports `undetected-chromedriver` to bypass Cloudflare and other bot detection systems. This is particularly useful for Infojobs and Glassdoor.

## Configuration

### Option 1: Environment Variable (Recommended)

Add to your `.env` file:

```env
USE_UNDETECTED_CHROMEDRIVER=true
```

### Option 2: Programmatic

```python
from scrapper.services.selenium.seleniumService import SeleniumService

# Use undetected-chromedriver
selenium = SeleniumService(useUndetected=True)

# Use standard Selenium
selenium = SeleniumService(useUndetected=False)
```

## Benefits

- **Bypasses Cloudflare**: Automatically handles most Cloudflare challenges
- **Reduces manual intervention**: Less need to solve CAPTCHAs manually
- **Better success rate**: Higher success rate for Infojobs and Glassdoor scraping

## How It Works

When `USE_UNDETECTED_CHROMEDRIVER=true`:
- Uses `undetected-chromedriver` instead of standard Selenium
- Automatically patches ChromeDriver to avoid detection
- Removes automation indicators that trigger bot detection

When `USE_UNDETECTED_CHROMEDRIVER=false` (default):
- Uses standard Selenium with stealth techniques
- Applies manual anti-detection measures

## Troubleshooting

If you still encounter Cloudflare challenges:
1. Increase wait times in scrapper code
2. Use a VPN or residential proxy
3. Reduce scraping frequency
4. Clear browser cache and cookies

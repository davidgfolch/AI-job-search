# flake8: noqa
LOGIN_PAGE = "https://es.indeed.com/account/login"

CSS_SEL_SEARCH_RESULT_ITEMS_FOUND = ".jobsearch-JobCountAndSortPane-jobCount > span:nth-child(1)"
CSS_SEL_GLOBAL_ALERT_HIDE = "div.ij-SearchListingPageContent-heading h1"

# LOGIN
CSS_SEL_LOGIN_EMAIL = 'input[type="email"]:not([style*="display: none"]):not([style*="display:none"]), input[name="email"]:not([style*="display: none"]):not([style*="display:none"]), input[autocomplete="email"]:not([style*="display: none"]):not([style*="display:none"]), input[placeholder*="email" i]:not([style*="display: none"]):not([style*="display:none"]), #ifl-InputFormField-3:not([style*="display: none"]):not([style*="display:none"]), .email-input, [data-testid="email-input"]'
CSS_SEL_LOGIN_PASSWORD = 'input[type="password"]:not([style*="display: none"]):not([style*="display:none"]), input[name="password"]:not([style*="display: none"]):not([style*="display:none"]), input[autocomplete="current-password"]:not([style*="display: none"]):not([style*="display:none"]), #ifl-InputFormField-6:not([style*="display: none"]):not([style*="display:none"]), .password-input, [data-testid="password-input"]'
CSS_SEL_LOGIN_SUBMIT = 'button[type="submit"], button[data-testid="submit"], button[data-tn="submit"]'
CSS_SEL_2FA_INPUT = 'input[name="code"], input[type="text"][placeholder*="code"]'
CSS_SEL_2FA_SUBMIT = 'button[type="submit"]'
CSS_SEL_GOOGLE_OTP_FALLBACK = "#auth-page-google-otp-fallback"
CSS_SEL_2FA_PASSCODE_INPUT = "#passcode-input"
CSS_SEL_2FA_VERIFY_SUBMIT = 'button[data-tn-element="otp-verify-login-submit-button"]'
CSS_SEL_WEBAUTHN_CONTINUE = "#pass-WebAuthn-continue-button"

# FALLBACK LOGIN SELECTORS (for different regions/layouts)
CSS_SEL_LOGIN_EMAIL_ALT = 'input[id*="email"], input[class*="email"], input[aria-label*="email" i], input[placeholder*="email" i]'
CSS_SEL_LOGIN_PASSWORD_ALT = 'input[id*="password"], input[class*="password"], input[aria-label*="password" i], input[placeholder*="password" i]'
CSS_SEL_2FA_INPUT_ALT = 'input[autocomplete="one-time-code"], input[name="verification_code"], input[name="code"], input[placeholder*="code" i], input[type="text"][data-testid="verification-code"]'
CSS_SEL_2FA_SUBMIT_ALT = 'button[data-testid="verify-code"], button[data-testid="submit"], button[type="submit"], input[type="submit"]'

# COOKIE CONSENT & MODAL CLOSE
CSS_SEL_COOKIE_ACCEPT = "#onetrust-accept-btn-handler, button[data-testid='accept-all'], .accept-cookies, [aria-label*='Accept' i]"
CSS_SEL_JOB_MODAL_CLOSE_BTN='div[aria-modal="true"] button[aria-label="cerrar"]'

# SEARCH
CSS_SEL_SEARCH_WHAT = "#text-input-what"
CSS_SEL_SEARCH_WHERE = "#text-input-where"
CSS_SEL_SEARCH_BTN = ".yosegi-InlineWhatWhere-primaryButton"
CSS_SEL_JOB_COUNT = ".jobsearch-JobCountAndSortPane-jobCount"
CSS_SEL_SORT_BY_DATE = "a[aria-labelledby='sortByLabel fechaLabel']"

# LIST
CSS_SEL_JOB_CARD = ".job_seen_beacon, .job_card, .jobsearch-SerpJobCard"
CSS_SEL_JOB_LI = ".job_seen_beacon"
CSS_SEL_JOB_LINK = ".jobTitle a, .jobTitle > a, h2.jobTitle > a, td.resultContent > div > h2 > a"
CSS_SEL_NEXT_PAGE_BUTTON = 'a[data-testid="pagination-page-next"]'
CSS_SEL_PAGINATION = ".css-1i78dwh, .pagination"

# JOB DETAIL
CSS_SEL_JOB_TITLE = "div.jobsearch-JobInfoHeader-title-container h2"
CSS_SEL_COMPANY = 'div[data-testid="inlineHeader-companyName"]'
CSS_SEL_LOCATION = 'div[data-testid="inlineHeader-companyLocation"]'
CSS_SEL_JOB_REQUIREMENTS = "#jobDescriptionText"
CSS_SEL_JOB_DESCRIPTION = "#jobDescriptionText"
CSS_SEL_JOB_EASY_APPLY = "#jobsearch-ViewJobButtons-container span.indeed-apply-status-not-applied button"
CSS_SEL_JOB_SALARY = "#salaryInfoAndJobType"
CSS_SEL_JOB_CLOSED = ""

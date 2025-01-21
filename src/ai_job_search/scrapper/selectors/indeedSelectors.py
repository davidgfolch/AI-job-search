# flake8: noqa
LOGIN_PAGE = 'https://www.infojobs.net/candidate/candidate-login/candidate-login.xhtml'

CSS_SEL_SECURITY_FILTER1 = 'body > div > div > div > div > div > div > p:nth-child(3) > span.break > a'
# CSS_SEL_SECURITY_FILTER1 = 'body > div > div > div > div > div > div > p:nth-child(3) > span.break > a'
CSS_SEL_SECURITY_FILTER1 = '#captcha-box span.geetest_radar_tip_content'
CSS_SEL_SECURITY_FILTER2 = '#captcha-box > div > div.geetest_wait'


CSS_SEL_SEARCH_RESULT_ITEMS_FOUND = '.jobsearch-JobCountAndSortPane-jobCount > span:nth-child(1)'
CSS_SEL_GLOBAL_ALERT_HIDE = 'div.ij-SearchListingPageContent-heading h1'


# LIST
CSS_SEL_JOB_LI = '.mainContentTable tr'
CSS_SEL_JOB_LINK = 'td.resultContent > div > h2 > a'
CSS_SEL_NEXT_PAGE_BUTTON = 'nav[role=navigation] > ul > li > a[data-testid="pagination-page-next"]'

# JOB DETAIL (IN LIST CLICK)
CSS_SEL_JOB_TITLE = 'div.jobsearch-JobInfoHeader-title-container h2'

CSS_SEL_COMPANY = 'div[data-company-name="true"] > span > a'
CSS_SEL_LOCATION = 'div[data-testid="inlineHeader-companyLocation"]'
CSS_SEL_JOB_REQUIREMENTS = '#mosaic-vjJobDetails'
CSS_SEL_JOB_DESCRIPTION = '#jobDescriptionText'
CSS_SEL_JOB_EASY_APPLY = '#indeedApplyButton'
CSS_SEL_JOB_CLOSED = 'div.jobs-details__main-content div.jobs-details-top-card__apply-error'  # No longer accepting applications

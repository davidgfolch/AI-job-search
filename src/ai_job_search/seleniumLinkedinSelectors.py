# flake8: noqa

CSS_SEL_SEARCH_RESULT_ITEMS_FOUND = 'div.scaffold-layout__list header div.jobs-search-results-list__title-heading div.jobs-search-results-list__subtitle'
CSS_SEL_MESSAGES_HIDE = 'aside[id="msg-overlay"] header > div.msg-overlay-bubble-header__controls > button'
CSS_SEL_GLOBAL_ALERT_HIDE = 'div.artdeco-global-alert section.artdeco-global-alert__body button.artdeco-global-alert__dismiss'


# LIST
CSS_SEL_NO_RESULTS = 'div.jobs-search-no-results-banner'
CSS_SEL_JOB_LI = 'div.scaffold-layout__list ul > li'
CSS_SEL_JOB_LI_IDX = f'{CSS_SEL_JOB_LI}:nth-child(##idx##)'
CSS_SEL_SUBTITLE = 'div.artdeco-entity-lockup__subtitle'
CSS_SEL_CAPTION = 'div.artdeco-entity-lockup__caption'
LI_JOB_TITLE_CSS_SUFFIX = 'div.artdeco-entity-lockup__title > a > span > strong'
CSS_SEL_JOB_LINK = f'{CSS_SEL_JOB_LI_IDX} > div > div > div > div > div > div > a'
CSS_SEL_NEXT_PAGE_BUTTON = 'div.jobs-search-pagination > button.jobs-search-pagination__button--next'

# JOB DETAIL (IN LIST CLICK)
CSS_SEL_JOB_HEADER = 'main h1 a'
CSS_SEL_JOB_DESCRIPTION = 'div.jobs-details__main-content article div.mt4'
CSS_SEL_JOB_EASY_APPLY = 'div.jobs-details__main-content button.jobs-apply-button svg[data-test-icon="linkedin-bug-xxsmall"]'
CSS_SEL_JOB_CLOSED = 'div.jobs-details__main-content div.jobs-details-top-card__apply-error'  # No longer accepting applications

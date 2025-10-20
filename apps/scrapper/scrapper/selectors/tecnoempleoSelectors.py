# flake8: noqa

CSS_SEL_SEARCH_RESULT_ITEMS_FOUND = 'div.container div.row div:nth-child(2) h1'
CSS_SEL_MESSAGES_HIDE = 'aside[id="msg-overlay"] header > div.msg-overlay-bubble-header__controls > button'
CSS_SEL_GLOBAL_ALERT_HIDE = 'div.artdeco-global-alert section.artdeco-global-alert__body button.artdeco-global-alert__dismiss'


# LIST
CSS_SEL_NO_RESULTS = 'div.container div.row div:nth-child(2) h3.h4'
CSS_SEL_MAIN_CONTAINER = '#wrapper > div.container > div > div.col-12.col-sm-12.col-md-12.col-lg-9 '
CSS_SEL_JOB_LI = f'{CSS_SEL_MAIN_CONTAINER} > div'
CSS_SEL_JOB_LI_IDX = f'{CSS_SEL_JOB_LI}:nth-child(##idx##) > div > div:nth-child(3)'
CSS_SEL_JOB_LI_IDX_LINK = f'{CSS_SEL_JOB_LI_IDX} > h3 > a'
CSS_SEL_PAGINATION_LINKS = f'{CSS_SEL_MAIN_CONTAINER} > nav > ul > li > a'

# JOB DETAIL
CSS_SEL_JOB_DETAIL = '#wrapper > section.m-0.pt-5 > div:nth-child(1) > div > div.col-12.col-md-7.col-lg-8.mb-5'
CSS_JOB_DETAIL_HEADER = f'{CSS_SEL_JOB_DETAIL} > div.row > div:nth-child(2)'
CSS_SEL_JOB_TITLE = f'{CSS_JOB_DETAIL_HEADER} > div > h1'
CSS_SEL_COMPANY = f'{CSS_JOB_DETAIL_HEADER} > a > span[itemprop=name]'

CSS_SEL_JOB_DESCRIPTION = f'{CSS_SEL_JOB_DETAIL} div[itemprop=description] p'
# Datos principales de la oferta
CSS_SEL_JOB_DATA = '#wrapper > section.m-0.pt-5 > div:nth-child(1) > div > div.col-12.col-md-5.col-lg-4.mb-5 > div > ul > li > span:nth-child(1)'
# CSS_SEL_JOB_EASY_APPLY = f'{CSS_SEL_JOB_DETAIL} div.jobs-details__main-content button.jobs-apply-button svg[data-test-icon="linkedin-bug-xxsmall"]'
# CSS_SEL_JOB_CLOSED = f'{CSS_SEL_JOB_DETAIL} div.jobs-details__main-content div.jobs-details-top-card__apply-error'  # No longer accepting applications

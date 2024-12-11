# flake8: noqa
LOGIN_PAGE = 'https://www.infojobs.net/candidate/candidate-login/candidate-login.xhtml'

CSS_SEL_SEARCH_RESULT_ITEMS_FOUND = 'div.ij-TemplateAdsPage-mainContainer > div.ij-SearchListingPageContent-heading > div.ij-Box.ij-SearchListingPageContent-heading-title > h1'
CSS_SEL_GLOBAL_ALERT_HIDE = 'div.ij-SearchListingPageContent-heading h1'


# LIST
CSS_SEL_JOB_LI = 'div.ij-SearchListingPageContent-main main ul > li'
CSS_SEL_JOB_LI_IDX = f'{CSS_SEL_JOB_LI}:nth-child(##idx##)'
CSS_SEL_JOB_LINK = f'{CSS_SEL_JOB_LI_IDX} div.sui-AtomCard-info div.ij-OfferCardContent-description h2 > a'
CSS_SEL_NEXT_PAGE_BUTTON = 'div.jobs-search-pagination > button.jobs-search-pagination__button--next'

# JOB DETAIL (IN LIST CLICK)
CSS_SEL_JOB_TITLE = '#prefijoPuesto'
CSS_SEL_COMPANY = '#main-wrapper div.heading-addons > div > div.content-type-text > a'
CSS_SEL_LOCATION = '#main-wrapper > div > div.container.container-slotbanner > div:nth-child(3) > div.panel-canvas.panel-rounded > div:nth-child(2) > div > div.col-8.col-6-medium > div > div > div:nth-child(1) > div > ul > li:nth-child(1)'

CSS_SEL_JOB_DETAIL = 'div.row div.panel-canvas'
CSS_SEL_JOB_REQUIREMENTS = f'{CSS_SEL_JOB_DETAIL} > ul'
CSS_SEL_JOB_DESCRIPTION = f'{CSS_SEL_JOB_DETAIL} > .highlight-text'
CSS_SEL_JOB_EASY_APPLY = f'{CSS_SEL_JOB_DETAIL} div.jobs-details__main-content button.jobs-apply-button svg[data-test-icon="linkedin-bug-xxsmall"]'
CSS_SEL_JOB_CLOSED = f'{CSS_SEL_JOB_DETAIL} div.jobs-details__main-content div.jobs-details-top-card__apply-error'  # No longer accepting applications

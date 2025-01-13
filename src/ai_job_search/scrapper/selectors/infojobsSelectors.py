# flake8: noqa
LOGIN_PAGE = 'https://www.infojobs.net/candidate/candidate-login/candidate-login.xhtml'

CSS_SEL_SECURITY_FILTER1 = 'body > div > div > div > div > div > div > p:nth-child(3) > span.break > a'
# CSS_SEL_SECURITY_FILTER1 = 'body > div > div > div > div > div > div > p:nth-child(3) > span.break > a'
CSS_SEL_SECURITY_FILTER1 = '#captcha-box span.geetest_radar_tip_content'
CSS_SEL_SECURITY_FILTER2 = '#captcha-box > div > div.geetest_wait'


CSS_SEL_SEARCH_RESULT_ITEMS_FOUND = 'div.ij-TemplateAdsPage-mainContainer > div.ij-SearchListingPageContent-heading > div.ij-Box.ij-SearchListingPageContent-heading-title > h1'
CSS_SEL_GLOBAL_ALERT_HIDE = 'div.ij-SearchListingPageContent-heading h1'


# LIST
CSS_SEL_JOB_LI = 'div.ij-SearchListingPageContent-main main > ul > li > .sui-AtomCard'
CSS_SEL_JOB_LINK = 'div.ij-OfferCardContent-description h2 > a'
CSS_SEL_NEXT_PAGE_BUTTON = 'div.ij-SearchListingPageContent-main > main ul.sui-MoleculePagination > li > button:has(svg)'

# JOB DETAIL (IN LIST CLICK)
CSS_SEL_JOB_TITLE = '#prefijoPuesto'
CSS_SEL_COMPANY = '#main-wrapper div.heading-addons a.link'
CSS_SEL_LOCATION = '#prefijoPoblacion'

CSS_SEL_JOB_DETAIL = 'div.row div.panel-canvas'
CSS_SEL_JOB_REQUIREMENTS = f'{CSS_SEL_JOB_DETAIL} > ul'
CSS_SEL_JOB_DESCRIPTION = f'{CSS_SEL_JOB_DETAIL} > .highlight-text'
CSS_SEL_JOB_EASY_APPLY = f'{CSS_SEL_JOB_DETAIL} #candidate_application'
CSS_SEL_JOB_CLOSED = f'{CSS_SEL_JOB_DETAIL} div.jobs-details__main-content div.jobs-details-top-card__apply-error'  # No longer accepting applications

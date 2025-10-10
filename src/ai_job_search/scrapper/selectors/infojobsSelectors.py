# flake8: noqa
LOGIN_PAGE = 'https://www.infojobs.net/candidate/candidate-login/candidate-login.xhtml'

CSS_SEL_SECURITY_FILTER1 = 'body > div > div > div > div > div > div > p:nth-child(3) > span.break > a'
# CSS_SEL_SECURITY_FILTER1 = 'body > div > div > div > div > div > div > p:nth-child(3) > span.break > a'
CSS_SEL_SECURITY_FILTER1 = '#captcha-box span.geetest_radar_tip_content'
CSS_SEL_SECURITY_FILTER2 = '#captcha-box > div > div.geetest_wait'


CSS_SEL_SEARCH_RESULT_ITEMS_FOUND = 'div.ij-TemplateAdsPage-mainContainer div.ij-SearchListingPageContent-heading div.ij-Box.ij-SearchListingPageContent-heading-title h1'
CSS_SEL_GLOBAL_ALERT_HIDE = 'div.ij-SearchListingPageContent-heading h1'


# LIST
# Note: there are some li with advertisements, they don't have the ij-OfferCardContent-description-title-link class'
CSS_SEL_JOB_LI = 'div.ij-SearchListingPageContent-list ul li.ij-List-item'
CSS_SEL_JOB_LINK = CSS_SEL_JOB_LI + ' div.sui-AtomCard-info h2 > a'
CSS_SEL_NEXT_PAGE_BUTTON = 'div.ij-Box.ij-SearchListingPageContent-main div.ij-Box.ij-TemplateAdsPage-row.ij-SearchListingPageContent-list div.ij-Box.ij-TemplateAdsPage-row div.ij-ComponentPagination ul.sui-MoleculePagination li.sui-MoleculePagination-item:last-child button.sui-AtomButton.sui-AtomButton--primary.sui-AtomButton--flat.sui-AtomButton--center'

# JOB DETAIL (IN LIST CLICK)
CSS_SEL_JOB_TITLE = 'h1'  # '#prefijoPuesto'
CSS_SEL_COMPANY = '.ij-OfferDetailHeader-companyLogo .ij-OfferDetailHeader-companyLogo-title .ij-OfferDetailHeader-companyLogo-companyName > a' # '#main-wrapper div.heading-addons a.link'
DETAILS_PREFIX = '.ij-OfferDetailHeader-detailsList'
CSS_SEL_LOCATION = 'div.ij-OfferDetailHeader-detailsList-column:nth-child(1) > div:nth-child(1) > p:nth-child(2)'  # '#main-wrapper div.heading-addons a.link'


CSS_SEL_JOB_DETAIL = '.ij-OfferDetailPage-mainContent-container' # '.ij-OfferDetailPage-mainContent-container > article:not(.no-printable)'
# No longer accepting applications
CSS_SEL_JOB_CLOSED = f'{CSS_SEL_JOB_DETAIL} div.jobs-details__main-content div.jobs-details-top-card__apply-error'

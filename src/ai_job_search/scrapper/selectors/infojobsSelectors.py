# flake8: noqa
LOGIN_PAGE = 'https://www.infojobs.net/candidate/candidate-login/candidate-login.xhtml'

CSS_SEL_SECURITY_FILTER1 = 'body > div > div > div > div > div > div > p:nth-child(3) > span.break > a'
# CSS_SEL_SECURITY_FILTER1 = 'body > div > div > div > div > div > div > p:nth-child(3) > span.break > a'
CSS_SEL_SECURITY_FILTER1 = '#captcha-box span.geetest_radar_tip_content'
CSS_SEL_SECURITY_FILTER2 = '#captcha-box > div > div.geetest_wait'


CSS_SEL_SEARCH_RESULT_ITEMS_FOUND = 'div.ij-TemplateAdsPage-mainContainer div.ij-SearchListingPageContent-heading div.ij-Box.ij-SearchListingPageContent-heading-title h1'
CSS_SEL_GLOBAL_ALERT_HIDE = 'div.ij-SearchListingPageContent-heading h1'


# LIST
CSS_SEL_JOB_LI = 'html body div#app div.sui-Layout-MediaQuery div.ij-Box.ij-Container.ij-Container-wrapper.ij-Container-centered.ij-TemplateAdsPage div.ij-Box.ij-Container.ij-Container-container.ij-TemplateAdsPage-mainContainer main.ij-Box.ij-TemplateAdsPage-main div.ij-Box.ij-SearchListingPageContent-main div.ij-Box.ij-TemplateAdsPage-row.ij-SearchListingPageContent-list ul.ij-List.ij-List--vertical.ij-List--spaced li.ij-List-item div.sui-AtomCard.sui-AtomCard-link.sui-AtomCard--rounded-l div.sui-AtomCard-info'
CSS_SEL_JOB_LINK = 'div.ij-OfferCardContent-description h2 > a'
CSS_SEL_NEXT_PAGE_BUTTON = 'html body div#app div.sui-Layout-MediaQuery div.ij-Box.ij-Container.ij-Container-wrapper.ij-Container-centered.ij-TemplateAdsPage div.ij-Box.ij-Container.ij-Container-container.ij-TemplateAdsPage-mainContainer main.ij-Box.ij-TemplateAdsPage-main div.ij-Box.ij-SearchListingPageContent-main div.ij-Box.ij-TemplateAdsPage-row.ij-SearchListingPageContent-list div.ij-Box.ij-TemplateAdsPage-row div.ij-ComponentPagination ul.sui-MoleculePagination li.sui-MoleculePagination-item button.sui-AtomButton.sui-AtomButton--primary.sui-AtomButton--flat.sui-AtomButton--center'

# JOB DETAIL (IN LIST CLICK)
CSS_SEL_JOB_TITLE = '#prefijoPuesto'
CSS_SEL_COMPANY = '#main-wrapper div.heading-addons a.link'
CSS_SEL_LOCATION = '#prefijoPoblacion'

CSS_SEL_JOB_DETAIL = 'div.row div.panel-canvas'
CSS_SEL_JOB_REQUIREMENTS = f'{CSS_SEL_JOB_DETAIL} > ul'
CSS_SEL_JOB_DESCRIPTION = f'{CSS_SEL_JOB_DETAIL} > .highlight-text'
CSS_SEL_JOB_EASY_APPLY = f'{CSS_SEL_JOB_DETAIL} #candidate_application'
CSS_SEL_JOB_CLOSED = f'{CSS_SEL_JOB_DETAIL} div.jobs-details__main-content div.jobs-details-top-card__apply-error'  # No longer accepting applications

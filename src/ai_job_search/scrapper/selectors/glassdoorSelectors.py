# flake8: noqa
# CSS_SEL_LOGIN_WITH_GOOGLE = '.social button[data-test="googleBtn"]'

CSS_SEL_SEARCH_RESULT_ITEMS_FOUND = 'div#left-column > div > h1'
CSS_SEL_COOKIES_ACCEPT = 'button#onetrust-accept-btn-handler'
CSS_SEL_GLOBAL_ALERT_HIDE = 'CSS_SEL_GLOBAL_ALERT_HIDE'


# LIST
#left-column > div.SearchResultsHeader_searchResultsHeader__uK15O > h1
CSS_SEL_NO_RESULTS = 'CSS_SEL_NO_RESULTS'
CSS_SEL_JOB_LI = 'div#left-column > div.JobsList_wrapper__EyUF6 > ul > li.JobsList_jobListItem__wjTHv'
CSS_SEL_JOB_LI_IDX = f'{CSS_SEL_JOB_LI}:nth-child(##idx##)'
CSS_SEL_COMPANY = '.EmployerProfile_compactEmployerName__9MGcV'
CSS_SEL_LOCATION = '.JobCard_location__Ds1fM'
LI_JOB_TITLE_CSS_SUFFIX = '.JobCard_jobTitle__GLyJ1'
# CSS_SEL_JOB_LINK = f'a[id*=job-title]'
CSS_SEL_JOB_LINK = 'a.JobCard_jobTitle__GLyJ1'
CSS_SEL_NEXT_PAGE_BUTTON = 'div#left-column > div.SimilarJobs_seeMoreJobs__t0df_ > div > a'

# JOB DETAIL (IN LIST CLICK)
CSS_SEL_JOB_DETAIL = 'div.JobDetails_jobDetailsContainer__y9P3L'
CSS_SEL_JOB_DESCRIPTION = f'{CSS_SEL_JOB_DETAIL} div.JobDetails_jobDescription__uW_fK'
CSS_SEL_JOB_EASY_APPLY = f'{CSS_SEL_JOB_DETAIL} header > div.JobDetails_webActionWrapper__ib_fm > div > button > span > div > svg'
CSS_SEL_JOB_CLOSED = f'{CSS_SEL_JOB_DETAIL} CSS_SEL_JOB_CLOSED'  # No longer accepting applications

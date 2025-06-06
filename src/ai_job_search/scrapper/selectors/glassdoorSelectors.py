# flake8: noqa
#LOGIN
CSS_SEL_PASSWORD_SUBMIT = 'form button[type=submit]'
CSS_SEL_INPUT_PASS = 'form input#inlineUserPassword'

#
CSS_SEL_SEARCH_RESULT_TOTAL = 'div#left-column h1'
CSS_SEL_COOKIES_ACCEPT = 'button#onetrust-accept-btn-handler'
CSS_SEL_GLOBAL_ALERT_HIDE = 'CSS_SEL_GLOBAL_ALERT_HIDE'
CSS_SEL_DIALOG_CLOSE = 'div[data-test="Modal-content"] button[data-test=job-alert-modal-close]'

# LIST
CSS_SEL_NO_RESULTS = 'CSS_SEL_NO_RESULTS'
CSS_SEL_JOB_LI = 'div#left-column > div.JobsList_wrapper__EyUF6 > ul > li.JobsList_jobListItem__wjTHv'
CSS_SEL_COMPANY = '.EmployerProfile_compactEmployerName__9MGcV'
CSS_SEL_COMPANY2 = '.EmployerProfile_employerNameContainer__ptolz h4'
CSS_SEL_LOCATION = 'header[data-test=job-details-header] div[data-test=location]'
LI_JOB_TITLE_CSS_SUFFIX = 'a.JobCard_jobTitle__GLyJ1'
CSS_SEL_NEXT_PAGE_BUTTON = 'div#left-column button[data-test="load-more"]'

# JOB DETAIL (IN LIST CLICK)
CSS_SEL_JOB_DETAIL = 'div.JobDetails_jobDetailsContainer__y9P3L'
CSS_SEL_JOB_TITLE = f'{CSS_SEL_JOB_DETAIL} h1'
CSS_SEL_JOB_DESCRIPTION = f'{CSS_SEL_JOB_DETAIL} div.JobDetails_jobDescription__uW_fK'
CSS_SEL_JOB_EASY_APPLY = f'{CSS_SEL_JOB_DETAIL} header > div.JobDetails_webActionWrapper__ib_fm > div > button > span > div > svg'

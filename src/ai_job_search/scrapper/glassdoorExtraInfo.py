from ai_job_search.scrapper import baseScrapper
from ai_job_search.scrapper.glassdoor import login
from ai_job_search.scrapper.selectors.glassdoorExtraInfoSelectors import (
    CSS_SEL_ROLES_COL, CSS_SEL_SALARY_COL)
from ai_job_search.scrapper.util import getAndCheckEnvVars
from ai_job_search.tools.terminalColor import red, yellow
from ai_job_search.viewer.util.stUtil import stripFields
from ai_job_search.scrapper.seleniumUtil import SeleniumUtil, sleep
from ai_job_search.tools.mysqlUtil import (MysqlUtil, updateFieldsQuery)

DEBUG = False
USER_EMAIL, USER_PWD, JOBS_SEARCH = getAndCheckEnvVars("GLASSDOOR")

WHERE = """WHERE ai_enriched and not scrapper_enriched
 and not (ignored or discarded or closed)
 and (salary is null or salary = '')"""
QRY_SELECT_JOBS_FOR_SCRAPPER_ENRICHMENT = f"""
SELECT distinct company
FROM jobs
{WHERE}
GROUP BY company"""

COLUMNS = stripFields('id,salary,comments,title')
SELECT_ALL_FROM_COMPANY = f"""select id,salary,comments,title
from jobs
{WHERE} and company=%(company)s
ORDER BY created desc"""
# TODO: move to .env
# https://www.glassdoor.es/Sueldo/knowmad-mood-Sueldos-E297765.htm
ROLES_MATCHING = ['Senior Software Engineer',
                  'Software Engineer',
                  'Ingeniero De Software',
                  'Arquitecto De Software',
                  'Software Architect']
QRY_UPDATE_SCRAPPER_ENRICHED_FLAG = """
UPDATE jobs set scrapper_enriched=1
where company = %(company)s"""

print('glassdoor extra-info scrapper init')
selenium = None
mysql = None


def run(company: str, overwriteSalaryId=None):
    """Login into glassdoor and get salaries for jobs"""
    global selenium, mysql
    selenium = None
    try:
        mysql = MysqlUtil()
        # TODO: COULD NOT PROCESS IN BATCH, AFTER SOME REQUESTS APPEARS A
        # SECURITY FILTER ANTI-ROBOT
        if (company):
            selenium = SeleniumUtil()
            login(selenium)
            processCompany(company, overwriteSalaryId)  # row[0]
        else:
            rows = mysql.fetchAll(QRY_SELECT_JOBS_FOR_SCRAPPER_ENRICHMENT)
            if len(rows) > 0:
                for row in rows:
                    try:
                        selenium = SeleniumUtil()
                        login(selenium)
                        sleep(2, 3)
                        processCompany(row[0], overwriteSalaryId)
                    except Exception as ex:
                        debug(f'ERROR In processCompany(): {ex}')
                        if DEBUG:
                            raise ex
                    finally:
                        selenium.close()
    except Exception as ex:
        debug(f'Exception {ex}')
        raise ex
    finally:
        mysql.close()
        if selenium is not None:
            selenium.close()


def processCompany(company, overwriteSalaryId):
    params = {'company': company}
    print(yellow(f'company = {company}'))
    # # click Companies -> li 2
    # url = 'https://www.glassdoor.es/Opiniones/index.htm'
    # if selenium.getUrl() != url:
    #     print(f'loading glassdoor page {url}...')
    #     selenium.loadPage(url)
    #     sleep(1, 2)
    # print('click companies...')
    # selenium.waitAndClick(CSS_SEL_COMPANIES)
    # print('search company...')
    # sleep(1, 2)
    # selenium.sendKeys(CSS_SEL_COMPANY_SEARCH, company)
    # selenium.waitAndClick(CSS_SEL_COMPANY_SEARCH_BUTTON)
    # sleep(1, 2)
    # elms = selenium.getElms('div#salaries a')
    # if len(elms) == 0:
    #     print(red("Could not find Salaries tab",
    #           yellow(" Solve security filter, and press a key...")))
    #     input()
    #     print(QRY_UPDATE_SCRAPPER_ENRICHED_FLAG)
    #     mysql.executeAndCommit(QRY_UPDATE_SCRAPPER_ENRICHED_FLAG, params)
    #     return
    # elms = selenium.waitAndClick('div#salaries a')
    # sleep(5, 6)

    # uriCompany = quote(company)
    # # url = f"https://www.glassdoor.es/Reviews/{uriCompany}-reviews-SRCH_KE0,10.htm"
    # url = f"https://www.glassdoor.com/Salary/{uriCompany}-Salaries-E2603649.htm"
    # selenium.loadPage(url)
    # selenium.waitUntilPageIsLoaded()
    # sleep(1, 2)
    # CSS_SEL_EMPLOYER = "p[class*=employer-header_employerHeader]"
    # selenium.waitUntil_presenceLocatedElement(CSS_SEL_EMPLOYER, 30)
    # employer = selenium.getText(CSS_SEL_EMPLOYER)
    # if not employer or employer.find(company) == -1:
    #     debug(yellow(f'Company page not loaded for {company}, ',
    #                  f'current is {employer}... IGNORING!'))
    #     return

    # click Companies -> li 2
    url = 'https://www.glassdoor.es/Opiniones/index.htm'
    if selenium.getUrl() != url:
        print(f'loading glassdor page {url}...')
        selenium.loadPage(url)
        sleep(1, 2)
    print('click companies...')
    selenium.waitAndClick(
        '.contentMenu__contentMenuStyles__contentMenuContainer > li:nth-child(2) > a')
    print('search company...')
    selenium.sendKeys(
        '#companyAutocomplete-companyDiscover-employerSearch', company)
    selenium.waitAndClick(
        '.companySearch__CompanySearchContainerStyles__container button')
    sleep(1, 2)
    elms = selenium.getElms('div#salaries a')
    if len(elms) == 0:
        print(red("Could not find Salaries tab"))
        print(QRY_UPDATE_SCRAPPER_ENRICHED_FLAG)
        mysql.executeAndCommit(QRY_UPDATE_SCRAPPER_ENRICHED_FLAG, params)
        return
    elms = selenium.waitAndClick('div#salaries a')
    sleep(5, 6)

    selenium.waitUntil_presenceLocatedElement(CSS_SEL_ROLES_COL, 30)
    elms = selenium.getElms('#onetrust-accept-btn-handler')
    if len(elms) > 0:
        print('cookies click...')
        elms[0].click()
    # note salary table is in its section, many other sections may appear
    debug('get salaries rows...')
    roleListElms = selenium.getElms(CSS_SEL_ROLES_COL)
    debug('before getting roles')
    roleElms = [elm for elm in roleListElms]
    roles = []
    for roleElm in roleElms:
        try:
            roles.append(roleElm.text)
        except Exception as ex:
            print(ex)
    debug(f'roles found {roles}')
    found = findFirstInList(roles, ROLES_MATCHING)
    if found:
        idx, role = found
        debug(f'found role {role}')
        salariesElms = selenium.getElms(CSS_SEL_SALARY_COL)
        salary = salariesElms[idx].text
        if overwriteSalaryId:
            query = f"select * from jobs where id={overwriteSalaryId}"
            print(query)
            rows = mysql.fetchAll(query)
            processRow(rows[0], company, role, salary)
        else:
            print(SELECT_ALL_FROM_COMPANY)
            rows = mysql.fetchAll(SELECT_ALL_FROM_COMPANY, params)
            total = len(rows)
            print(f'Jobs to update: {total}')
            for row in rows:
                processRow(row, company, role, salary)
        print()
        return
    print(yellow('NO matching role found'))


def processRow(row, company, role, salary):
    id = row[COLUMNS.index('id')]
    title = row[COLUMNS.index('title')]
    comments = row[COLUMNS.index('comments')]
    if not isinstance(comments, str):
        comments = baseScrapper.join(
            comments.decode('utf-8'), '\n') if comments else ''
    comments += ' Salary scrapped from Glassdoor: '+selenium.getUrl()
    params = {'scrapper_enriched': 1,
              'salary': f'From glassdoor: {role} - {salary}',
              'comments': comments}
    query, params = updateFieldsQuery([id], params)
    print(params)
    if mysql.executeAndCommit(query, params) > 0:
        print(yellow(f"UPDATED salary & comments for: {company} - {title}"))
    else:
        print(QRY_UPDATE_SCRAPPER_ENRICHED_FLAG)
        mysql.executeAndCommit(QRY_UPDATE_SCRAPPER_ENRICHED_FLAG,
                               {'company': company})


def findFirstInList(list: list[str], keywords: list[str]):
    for search in keywords:
        found = [(idx, r) for idx, r in enumerate(list) if r.find(search) > -1]
        if len(found) > 0:
            return found[0]


def debug(msg: str = ''):
    baseScrapper.debug(DEBUG, msg)


if __name__ == "__main__":
    run('')

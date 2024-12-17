import time
from ai_job_search.scrapper import baseScrapper
from ai_job_search.scrapper.glassdoor import login
from ai_job_search.scrapper.util import getAndCheckEnvVars
from ai_job_search.tools.terminalColor import red, yellow
from ai_job_search.viewer.util.stUtil import stripFields
from ai_job_search.scrapper.seleniumUtil import SeleniumUtil
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
    selenium = SeleniumUtil()
    try:
        mysql = MysqlUtil()
        # TODO: COULD NOT PROCESS IN BATCH, AFTER SOME REQUESTS APPEARS A
        # SECURITY FILTER ANTI-ROBOT
        if (company):
            login(selenium)
            processCompany(company, overwriteSalaryId)  # row[0]
        else:
            rows = mysql.fetchAll(QRY_SELECT_JOBS_FOR_SCRAPPER_ENRICHMENT)
            if len(rows) > 0:
                login(selenium)
                time.sleep(2)
                for idx, row in enumerate(rows):
                    try:
                        processCompany(row[0], overwriteSalaryId)
                    except Exception as ex:
                        debug(f'ERROR In processCompany(): {ex}')
                        if DEBUG:
                            raise ex
                    if idx % 5 == 0:
                        selenium.close()
                        selenium = SeleniumUtil()
                        login(selenium)
    except Exception as ex:
        debug(f'Exception {ex}')
        raise ex
    finally:
        mysql.close()
        selenium.close()


def processCompany(company, overwriteSalaryId):
    params = {'company': company}
    print(yellow(f'company = {company}'))
    # click Companies -> li 2
    url = 'https://www.glassdoor.es/Opiniones/index.htm'
    if selenium.getUrl() != url:
        print(f'loading glassdor page {url}...')
        selenium.loadPage(url)
        time.sleep(1)
    print('click companies...')
    selenium.waitAndClick(
        '.contentMenu__contentMenuStyles__contentMenuContainer > li:nth-child(2) > a')
    print('search company...')
    selenium.sendKeys(
        '#companyAutocomplete-companyDiscover-employerSearch', company)
    selenium.waitAndClick(
        '.companySearch__CompanySearchContainerStyles__container button')
    time.sleep(1)
    elms = selenium.getElms('div#salaries a')
    if len(elms) == 0:
        print(red("Could not find Salaries tab"))
        print(QRY_UPDATE_SCRAPPER_ENRICHED_FLAG)
        mysql.executeAndCommit(QRY_UPDATE_SCRAPPER_ENRICHED_FLAG, params)
        return
    elms = selenium.waitAndClick('div#salaries a')
    time.sleep(5)
    elms = selenium.getElms('#onetrust-accept-btn-handler')
    if len(elms) > 0:
        print('cookies click...')
        elms[0].click()
    # note salary table is in its section, many other sections may appear
    print('get salaries rows...')
    cssSelTableRows = 'section.salarylist_SalaryListContainer__6rbaC > table > tbody > tr'
    roleListElms = selenium.getElms(f'{cssSelTableRows} > td:nth-child(1) > a')
    debug('before getting roles')
    roleElms = [elm for elm in roleListElms]
    roles = []
    for roleElm in roleElms:
        try:
            roles.append(roleElm.text)
        except Exception as ex:
            print(ex)
    print('roles found', roles)
    found = findFirstInList(roles, ROLES_MATCHING)
    if found:
        idx, role = found
        print('found role', role)
        cssSelSalary = f'{cssSelTableRows} td:nth-child(2) p.salarylist_total-pay-range__ECY78'
        salariesElms = selenium.getElms(cssSelSalary)
        salary = salariesElms[idx].text
        print(SELECT_ALL_FROM_COMPANY)
        if overwriteSalaryId:
            rows = mysql.fetchAll(
                f"select * from jobs where id={overwriteSalaryId}")
            processRow(rows[0], company, role, salary)
        else:
            rows = mysql.fetchAll(SELECT_ALL_FROM_COMPANY, params)
            total = len(rows)
            print(f'Jobs to update: {total}')
            for row in rows:
                processRow(row, company, role, salary)
        print()


def processRow(row, company, role, salary):
    id = row[COLUMNS.index('id')]
    title = row[COLUMNS.index('title')]
    comments = row[COLUMNS.index('comments')]
    if not isinstance(comments, str):
        comments = baseScrapper.join(
            comments.decode('utf-8'), '\n') if comments else ''
    comments += 'Salary scrapped from Glassdoor: '+selenium.getUrl()
    params = {'scrapper_enriched': 1,
              'salary': f'From glassdoor: {role} - {salary}',
              'comments': comments}
    query, params = updateFieldsQuery([id], params)
    print(params)
    if mysql.executeAndCommit(query, params) > 0:
        print(yellow(f"UPDATED salary & comments for: {company} - {title}"))
    else:
        print(QRY_UPDATE_SCRAPPER_ENRICHED_FLAG)
        mysql.executeAndCommit(QRY_UPDATE_SCRAPPER_ENRICHED_FLAG, params)


def findFirstInList(list: list[str], keywords: list[str]):
    for search in keywords:
        found = [(idx, r) for idx, r in enumerate(list) if r.find(search) > -1]
        if len(found) > 0:
            return found[0]


def debug(msg: str = ''):
    baseScrapper.debug(DEBUG, msg)


if __name__ == "__main__":
    run('')

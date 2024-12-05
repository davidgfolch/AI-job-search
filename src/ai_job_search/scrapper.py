from ai_job_search.scrapper.seleniumUtil import SeleniumUtil
import ai_job_search.scrapper.seleniumLinkedin as linkedIn


print('populateDb init')
seleniumUtil = SeleniumUtil()
linkedIn.run(seleniumUtil)

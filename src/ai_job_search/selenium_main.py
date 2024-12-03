from ai_job_search.seleniumUtil import SeleniumUtil
import seleniumLinkedin


print('populateDb init')
seleniumUtil = SeleniumUtil()
seleniumLinkedin.run(seleniumUtil)

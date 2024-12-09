from ai_job_search.scrapper.seleniumUtil import SeleniumUtil
import ai_job_search.scrapper.seleniumLinkedin as linkedIn
import ai_job_search.scrapper.seleniumGlassdoor as glassdoor


print('populateDb init')
seleniumUtil = SeleniumUtil()
linkedIn.run(seleniumUtil)
#glassdoor.run(seleniumUtil)

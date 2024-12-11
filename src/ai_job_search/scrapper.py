from ai_job_search.scrapper.seleniumUtil import SeleniumUtil
import ai_job_search.scrapper.seleniumLinkedin as linkedIn
import ai_job_search.scrapper.seleniumGlassdoor as glassdoor
import ai_job_search.scrapper.seleniumInfojobs as infojobs


print('populateDb init')
seleniumUtil = SeleniumUtil()
linkedIn.run(seleniumUtil)
#glassdoor.run(seleniumUtil)
#infojobs.run(seleniumUtil)

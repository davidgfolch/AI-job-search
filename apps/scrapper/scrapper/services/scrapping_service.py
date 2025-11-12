from typing import List, Dict, Any
from ..interfaces.scrapper_interface import ScrapperInterface
from ..interfaces.job_storage_interface import JobStorageInterface
from ..seleniumUtil import SeleniumUtil
from ..baseScrapper import printScrapperTitle
from commonlib.terminalColor import green, yellow, red

class ScrappingService:
    def __init__(self, scrapper: ScrapperInterface, storage: JobStorageInterface):
        self.scrapper = scrapper
        self.storage = storage

    def executeScrapping(self, selenium: SeleniumUtil, keywordsList: List[str], preloadOnly: bool = False) -> Dict[str, Any]:
        printScrapperTitle(self.scrapper.getSiteName(), preloadOnly)
        results = {
            'site': self.scrapper.getSiteName(),
            'total_processed': 0,
            'total_saved': 0,
            'total_duplicates': 0,
            'errors': [],
            'login_success': False
        }
        try:
            if not hasattr(self.scrapper, 'login_success'):
                loginResult = self.scrapper.login(selenium)
                results['login_success'] = loginResult
                self.scrapper.login_success = loginResult
                if not loginResult:
                    return results
            else:
                results['login_success'] = self.scrapper.login_success
            if preloadOnly:
                return results
            for keywords in keywordsList:
                keywordResults = self._processKeywords(selenium, keywords.strip())
                results['total_processed'] += keywordResults['processed']
                results['total_saved'] += keywordResults['saved']
                results['total_duplicates'] += keywordResults['duplicates']
                results['errors'].extend(keywordResults['errors'])
            self.storage.mergeDuplicates()
        except Exception as e:
            results['errors'].append(f"Critical error: {str(e)}")
            print(red(f"Critical error in scrapping service: {e}"))
        return results

    def _processKeywords(self, selenium: SeleniumUtil, keywords: str) -> Dict[str, Any]:
        results = {
            'keywords': keywords,
            'processed': 0,
            'saved': 0,
            'duplicates': 0,
            'errors': []
        }
        try:
            jobs = self.scrapper.searchJobs(selenium, keywords)
            for jobData in jobs:
                results['processed'] += 1
                if self._isDuplicateJob(jobData):
                    results['duplicates'] += 1
                    print(yellow(f"Job id={jobData.get('job_id', 'unknown')} already exists in DB, IGNORED."))
                    continue
                if self._saveJob(jobData):
                    results['saved'] += 1
                    print(green(f"INSERTED {jobData.get('job_id', 'unknown')}!"), flush=True)
                else:
                    results['errors'].append(f"Failed to save job {jobData.get('job_id', 'unknown')}")
        except Exception as e:
            results['errors'].append(f"Error processing keywords '{keywords}': {str(e)}")
            print(red(f"Error processing keywords '{keywords}': {e}"))
        return results

    def _isDuplicateJob(self, jobData: Dict[str, Any]) -> bool:
        jobId = jobData.get('job_id')
        if not jobId:
            return False
        return self.storage.jobExists(str(jobId))

    def _saveJob(self, jobData: Dict[str, Any]) -> bool:
        try:
            requiredFields = ['job_id', 'title', 'company', 'url', 'markdown']
            for field in requiredFields:
                if not jobData.get(field):
                    print(red(f"Missing required field: {field}"))
                    return False
            savedId = self.storage.saveJob(jobData)
            if savedId:
                print(green(f'INSERTED {savedId}!'), end='')
                self.storage.mergeDuplicates()
            return savedId is not None
        except Exception as e:
            print(red(f"Error saving job: {e}"))
            return False
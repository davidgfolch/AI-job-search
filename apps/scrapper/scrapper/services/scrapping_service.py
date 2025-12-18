from typing import List, Dict, Any, Callable
from ..interfaces.scrapper_interface import ScrapperInterface
from ..interfaces.job_storage_interface import JobStorageInterface
from ..services.selenium.seleniumService import SeleniumService
from ..baseScrapper import printScrapperTitle
from commonlib.terminalColor import green, yellow, red
from ..persistence_manager import PersistenceManager


class ScrappingService:
    def __init__(self, scrapper: ScrapperInterface, storage: JobStorageInterface):
        self.scrapper: ScrapperInterface = scrapper
        self.storage: JobStorageInterface = storage

    def executeScrapping(self, selenium: SeleniumService, keywordsList: List[str], preloadOnly: bool = False, persistenceManager: PersistenceManager = None) -> Dict[str, Any]:
        printScrapperTitle(self.scrapper.getSiteName(), preloadOnly)
        results = {
            'site': self.scrapper.getSiteName(),
            'total_processed': 0,
            'total_saved': 0,
            'total_duplicates': 0,
            'errors': [],
            'login_success': False
        }
        
        saved_state = {}
        if persistenceManager:
            saved_state = persistenceManager.get_state(self.scrapper.getSiteName())
        
        saved_keyword = saved_state.get('keyword')
        saved_page = saved_state.get('page', 1)

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
            
            skip = True if saved_keyword else False
            
            for keywords in keywordsList:
                current_keyword = keywords.strip()
                start_page = 1
                
                if saved_keyword:
                    if saved_keyword == current_keyword:
                        skip = False
                        start_page = saved_page
                    elif skip:
                        print(yellow(f"Skipping keyword '{current_keyword}' (already processed)"))
                        continue
                
                def on_page_complete(page_num):
                    if persistenceManager:
                        persistenceManager.update_state(self.scrapper.getSiteName(), current_keyword, page_num + 1)

                keywordResults = self._processKeywords(selenium, current_keyword, start_page, on_page_complete)
                results['total_processed'] += keywordResults['processed']
                results['total_saved'] += keywordResults['saved']
                results['total_duplicates'] += keywordResults['duplicates']
                results['errors'].extend(keywordResults['errors'])
                
                # After finishing a keyword, reset page for next keyword
                if persistenceManager:
                     # We might want to clear state or set to next keyword page 1, 
                     # but since we loop, the next iteration will set the new keyword.
                     # However, if we crash between keywords, we want to know we finished the previous one.
                     # Setting page to 1 for the *next* keyword would be ideal, but we don't know it yet easily here without lookahead.
                     # But since we update state on page complete, if we finish the loop, we are effectively done with this keyword.
                     pass

            self.storage.mergeDuplicates()
            # If we finished all keywords, we can clear the state for this site
            if persistenceManager:
                persistenceManager.clear_state(self.scrapper.getSiteName())

        except Exception as e:
            results['errors'].append(f"Critical error: {str(e)}")
            print(red(f"Critical error in scrapping service: {e}"))
        return results

    def _processKeywords(self, selenium: SeleniumService, keywords: str, start_page: int = 1, on_page_complete: Callable[[int], None] = None) -> Dict[str, Any]:
        results = {
            'keywords': keywords,
            'processed': 0,
            'saved': 0,
            'duplicates': 0,
            'errors': []
        }
        try:
            jobs = self.scrapper.searchJobs(selenium, keywords, start_page, on_page_complete)
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
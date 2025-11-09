from typing import List, Dict, Any
from ..interfaces.scrapper_interface import ScrapperInterface
from ..interfaces.job_storage_interface import JobStorageInterface
from ..seleniumUtil import SeleniumUtil
from commonlib.terminalColor import green, yellow, red

class ScrappingService:
    """Service handling scrapping business logic following SRP"""
    
    def __init__(self, scrapper: ScrapperInterface, storage: JobStorageInterface):
        self.scrapper = scrapper
        self.storage = storage
    
    def execute_scrapping(self, selenium: SeleniumUtil, keywords_list: List[str], preload_only: bool = False) -> Dict[str, Any]:
        """Execute scrapping process with business logic"""
        results = {
            'site': self.scrapper.get_site_name(),
            'total_processed': 0,
            'total_saved': 0,
            'total_duplicates': 0,
            'errors': []
        }
        
        try:
            # Login phase
            if preload_only:
                success = self.scrapper.login(selenium)
                results['login_success'] = success
                return results
            
            # Scrapping phase
            for keywords in keywords_list:
                keyword_results = self._process_keywords(selenium, keywords.strip())
                results['total_processed'] += keyword_results['processed']
                results['total_saved'] += keyword_results['saved']
                results['total_duplicates'] += keyword_results['duplicates']
                results['errors'].extend(keyword_results['errors'])
            
            # Merge duplicates after all scrapping
            self.storage.merge_duplicates()
            
        except Exception as e:
            results['errors'].append(f"Critical error: {str(e)}")
            print(red(f"Critical error in scrapping service: {e}"))
        
        return results
    
    def _process_keywords(self, selenium: SeleniumUtil, keywords: str) -> Dict[str, Any]:
        """Process jobs for specific keywords"""
        results = {
            'keywords': keywords,
            'processed': 0,
            'saved': 0,
            'duplicates': 0,
            'errors': []
        }
        
        try:
            print(yellow(f'Processing keywords: {keywords}'))
            jobs = self.scrapper.search_jobs(selenium, keywords)
            
            for job_data in jobs:
                results['processed'] += 1
                
                if self._is_duplicate_job(job_data):
                    results['duplicates'] += 1
                    print(yellow(f"Job {job_data.get('job_id', 'unknown')} already exists, skipped"))
                    continue
                
                if self._save_job(job_data):
                    results['saved'] += 1
                    print(green(f"Job {job_data.get('job_id', 'unknown')} saved successfully"))
                else:
                    results['errors'].append(f"Failed to save job {job_data.get('job_id', 'unknown')}")
        
        except Exception as e:
            results['errors'].append(f"Error processing keywords '{keywords}': {str(e)}")
            print(red(f"Error processing keywords '{keywords}': {e}"))
        
        return results
    
    def _is_duplicate_job(self, job_data: Dict[str, Any]) -> bool:
        """Check if job is duplicate"""
        job_id = job_data.get('job_id')
        if not job_id:
            return False
        return self.storage.job_exists(str(job_id))
    
    def _save_job(self, job_data: Dict[str, Any]) -> bool:
        """Save job with validation"""
        try:
            # Validate required fields
            required_fields = ['job_id', 'title', 'company', 'url', 'markdown']
            for field in required_fields:
                if not job_data.get(field):
                    print(red(f"Missing required field: {field}"))
                    return False
            
            # Save job
            saved_id = self.storage.save_job(job_data)
            return saved_id is not None
            
        except Exception as e:
            print(red(f"Error saving job: {e}"))
            return False
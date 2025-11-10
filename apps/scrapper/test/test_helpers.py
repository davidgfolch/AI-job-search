"""Test helper classes for scrapper tests"""

from commonlib.terminalColor import green, printHR, red, yellow
from commonlib.mysqlUtil import MysqlUtil


class BaseScrapper:
    """Base scrapper class for job tracking and database operations (test helper)"""
    
    def __init__(self, name: str = "BaseScrapper", url: str = ""):
        self.name = name
        self.url = url
        self.jobsFound = 0
        self.jobsSaved = 0
        self.jobsDuplicates = 0
        self.jobsErrors = 0
    
    def saveJob(self, job_data):
        """Save job to database and update counters"""
        if not job_data:
            self.jobsErrors += 1
            return False
        
        try:
            with MysqlUtil() as mysql:
                result = mysql.insertJob(job_data)
                if result:
                    self.jobsSaved += 1
                    return True
                else:
                    self.jobsDuplicates += 1
                    return False
        except Exception:
            self.jobsErrors += 1
            return False
    
    def printStats(self):
        """Print scrapper statistics"""
        printHR(green)
        if self.jobsFound == 0:
            print(green(f'{self.name}: No jobs processed'))
        else:
            print(green(f'{self.name} - Jobs found: {self.jobsFound}'))
            print(yellow(f'Jobs saved: {self.jobsSaved}'))
            print(yellow(f'Jobs duplicates: {self.jobsDuplicates}'))
            print(red(f'Jobs errors: {self.jobsErrors}'))
        printHR(green)
    
    def getStats(self):
        """Get scrapper statistics as dictionary"""
        return {
            'name': self.name,
            'jobsFound': self.jobsFound,
            'jobsSaved': self.jobsSaved,
            'jobsDuplicates': self.jobsDuplicates,
            'jobsErrors': self.jobsErrors
        }

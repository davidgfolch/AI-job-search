"""Test helper functions for merge duplicates tests"""
from commonlib.mysqlUtil import MysqlUtil


def mergeDuplicates():
    """Main function to merge duplicates"""
    try:
        with MysqlUtil() as mysql:
            from commonlib.mergeDuplicates import getSelect
            rows = mysql.fetchAll(getSelect())
            if len(rows) == 0:
                return 0
            
            # Extract jobs with proper structure: (id, title, company)
            jobs = []
            for row in rows:
                ids = row[1].split(',')  # row[1] contains comma-separated ids
                for job_id in ids:
                    jobs.append((int(job_id), row[2], row[3]))  # id, title, company
            
            duplicate_groups = findDuplicates(jobs)
            
            for group in duplicate_groups:
                primary_job = group[0]
                duplicate_jobs = group[1:]
                
                mergeJobData(primary_job, duplicate_jobs)
                updateJobReferences(primary_job[0], [job[0] for job in duplicate_jobs])
                
                for job in duplicate_jobs:
                    deleteJob(job[0])
            
            return len(duplicate_groups)
    except Exception:
        raise


def findDuplicates(jobs):
    """Find duplicate jobs based on title and company"""
    if not jobs:
        return []
    
    duplicates = {}
    
    for job in jobs:
        # Normalize title and company for comparison (case insensitive)
        # job is a tuple: (id, title, company)
        title = (job[1] or '') if len(job) > 1 else ''
        company = (job[2] or '') if len(job) > 2 else ''
        title = title.lower().strip() if isinstance(title, str) else ''
        company = company.lower().strip() if isinstance(company, str) else ''
        key = (title, company)
        
        if key not in duplicates:
            duplicates[key] = []
        duplicates[key].append(job)
    
    # Return only groups with more than one job
    return [group for group in duplicates.values() if len(group) > 1]


def mergeJobData(primary_job, duplicate_jobs):
    """Merge job data from duplicates into primary job"""
    try:
        with MysqlUtil() as mysql:
            # Simple merge implementation - in real scenario would merge fields
            mysql.executeAndCommit("UPDATE jobs SET merged = NOW() WHERE id = %s", (primary_job[0],))
    except Exception:
        raise


def updateJobReferences(primary_job_id, duplicate_job_ids):
    """Update references to point to primary job"""
    try:
        with MysqlUtil() as mysql:
            for job_id in duplicate_job_ids:
                mysql.executeAndCommit("UPDATE job_references SET job_id = %s WHERE job_id = %s", 
                            (primary_job_id, job_id))
    except Exception:
        raise


def deleteJob(job_id):
    """Delete a job from database"""
    try:
        with MysqlUtil() as mysql:
            mysql.executeAndCommit("DELETE FROM jobs WHERE id = %s", (job_id,))
    except Exception:
        raise


class MergeDuplicatesProcessor:
    """Processor class for merging duplicates"""
    
    def __init__(self):
        self.processed_count = 0
        self.merged_count = 0
        self.errors = []
    
    def process(self):
        """Process duplicate merging"""
        try:
            with MysqlUtil() as mysql:
                from commonlib.mergeDuplicates import getSelect
                rows = mysql.fetchAll(getSelect())
                self.processed_count = len(rows)
                
                # Extract jobs with proper structure: (id, title, company)
                jobs = []
                for row in rows:
                    ids = row[1].split(',')  # row[1] contains comma-separated ids
                    for job_id in ids:
                        jobs.append((int(job_id), row[2], row[3]))  # id, title, company
                
                duplicate_groups = findDuplicates(jobs)
                
                for group in duplicate_groups:
                    try:
                        self._merge_duplicate_group(group)
                        self.merged_count += 1
                    except Exception as e:
                        self.errors.append(str(e))
                
                return self.merged_count
        except Exception as e:
            self.errors.append(str(e))
            raise
    
    def _merge_duplicate_group(self, group):
        """Merge a group of duplicate jobs"""
        primary_job = group[0]
        duplicate_jobs = group[1:]
        
        mergeJobData(primary_job, duplicate_jobs)
        updateJobReferences(primary_job[0], [job[0] for job in duplicate_jobs])
        
        for job in duplicate_jobs:
            deleteJob(job[0])
    
    def get_stats(self):
        """Get processing statistics"""
        return {
            'processed_count': self.processed_count,
            'merged_count': self.merged_count,
            'error_count': len(self.errors),
            'errors': self.errors
        }

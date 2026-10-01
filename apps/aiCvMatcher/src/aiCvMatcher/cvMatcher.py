from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from commonlib.sql.mysqlUtil import MysqlUtil
from commonlib.stopWatch import StopWatch
from commonlib.environmentUtil import getEnv, getEnvBool
from commonlib.stringUtil import removeExtraEmptyLines
from commonlib.sqlUtil import emptyToNone, maxLen
from commonlib.cv_loader import CVLoader
from commonlib.aiEnrichRepository import AiEnrichRepository
from commonlib.observability import get_logger

CV_LOCATION = './cv/cv.txt'

logger = get_logger("aiCvMatcher.cvMatcher")


class FastCVMatcher:
    _instance = None
    _model = None
    _cv_embedding = None
    _cv_content = None
    _cv_loader = None
    
    stopWatch = StopWatch()
    totalCount = 0
    jobErrors = set()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FastCVMatcher, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        logger.info("model.loading", model='all-MiniLM-L6-v2')
        self._model = SentenceTransformer('all-MiniLM-L6-v2') 
        logger.info("model.loaded", model='all-MiniLM-L6-v2')
        self._cv_loader = CVLoader(cv_location=CV_LOCATION, enabled=getEnvBool('AI_CVMATCHER_ENABLED'))

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = FastCVMatcher()
        return cls._instance

    def process_db_jobs(self) -> int:
        if not getEnvBool('AI_CVMATCHER_ENABLED'):
            return 0
        if not self._load_cv_content():
            return 0
        with MysqlUtil() as mysql:
            repo = AiEnrichRepository(mysql)
            total = repo.count_pending_cv_match()
            if total == 0:
                return total
            limit = int(getEnv('AI_CVMATCHER_LIMIT', '100'))
            job_ids = repo.get_pending_cv_match_ids(limit)
            logger.info("jobs.batch_started", total=total, limit=limit, count=len(job_ids))
            for idx, id in enumerate(job_ids):
                self.stopWatch.start()
                try:
                    job = repo.get_job_to_match_cv(id)
                    if job is None:
                        continue
                    title = job[1]
                    company = job[3]
                    markdown = removeExtraEmptyLines(job[2].decode("utf-8") if isinstance(job[2], bytes) else job[2])
                    logger.debug("job.started", job_id=id, index=idx+1, total=total, title=title, company=company, input_length=len(markdown))
                    result = self.match(f'# {title} \n {markdown}')
                    logger.debug("job.result", job_id=id, index=idx+1, total=total, cv_match_percentage=result.get('cv_match_percentage'))
                    self._save_result(repo, id, result)
                except (Exception, KeyboardInterrupt) as ex:
                    self._save_error(repo, id, title, company, ex)
                self.totalCount += 1
                self.stopWatch.end()
            self._print_footer(total, idx)
            return total-idx

    def _load_cv_content(self) -> bool:
        if self._cv_content:
            return True
        if self._cv_loader.load_cv_content():
            self._cv_content = self._cv_loader.get_content()
            self._cv_embedding = self._model.encode([self._cv_content])
            logger.info("cv.context_loaded", location=CV_LOCATION, chars=len(self._cv_content))
            return True
        return False

    def match(self, job_description: str) -> dict:
        if self._cv_embedding is None:
             return {"cv_match_percentage": 0}
        try:
            job_embedding = self._model.encode([job_description])
            similarity = cosine_similarity(self._cv_embedding, job_embedding)[0][0]
            percentage = int(max(0, similarity) * 100)
            return {"cv_match_percentage": percentage}
        except Exception:
            logger.exception("match.failed")
            return {"cv_match_percentage": 0}

    def _save_result(self, repo: AiEnrichRepository, id, result: dict):
        repo.update_cv_match(id, result.get('cv_match_percentage'))

    def _save_error(self, repo: AiEnrichRepository, id, title, company, ex):
        logger.exception("job.failed", job_id=id, title=title, company=company)
        self.jobErrors.add((id, f'{title} - {company}: {ex}'))
        repo.update_enrichment_error(id, str(ex), False)
        logger.warning("job.error_saved", job_id=id, cv_match_percentage=-1)

    def _print_footer(self, total, idx):
        logger.info("jobs.batch_completed", processed=idx+1, total=total, total_processed=self.totalCount)
        if self.jobErrors:
            logger.warning("jobs.batch_errors", job_errors=len(self.jobErrors))

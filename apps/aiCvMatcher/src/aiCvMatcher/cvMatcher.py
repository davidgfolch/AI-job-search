import json
import traceback
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from commonlib.mysqlUtil import MysqlUtil
from commonlib.stopWatch import StopWatch
from commonlib.terminalColor import yellow, red, cyan, green, printHR
from commonlib.environmentUtil import getEnv, getEnvBool
from commonlib.stringUtil import removeExtraEmptyLines
from commonlib.dateUtil import getDatetimeNowStr
from commonlib.sqlUtil import emptyToNone, maxLen
from commonlib.cv_loader import CVLoader
from commonlib.aiEnrichRepository import AiEnrichRepository

CV_LOCATION = './cv/cv.txt'


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
        print("Loading embedding model (this may take a while significantly on first run)...")
        self._model = SentenceTransformer('all-MiniLM-L6-v2') 
        print(cyan("Embedding model loaded."))
        self._cv_loader = CVLoader(cv_location=CV_LOCATION, enabled=getEnvBool('AI_CV_MATCH'))

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = FastCVMatcher()
        return cls._instance

    def process_db_jobs(self) -> int:
        if not getEnvBool('AI_CV_MATCH'):
            return 0
        if not self._load_cv_content():
            return 0
        with MysqlUtil() as mysql:
            repo = AiEnrichRepository(mysql)
            total = repo.count_pending_cv_match()
            if total == 0:
                return total
            print()
            limit = int(getEnv('AI_CV_MATCH_NEW_LIMIT', '100'))
            job_ids = repo.get_pending_cv_match_ids(limit)
            print(yellow(f'{job_ids}'))
            for idx, id in enumerate(job_ids):
                self.stopWatch.start()
                try:
                    job = repo.get_job_to_match_cv(id)
                    if job is None:
                        continue
                    title = job[1]
                    company = job[3]
                    markdown = removeExtraEmptyLines(job[2].decode("utf-8") if isinstance(job[2], bytes) else job[2])
                    print(green(f'AI CV match job {idx+1}/{total} - {getDatetimeNowStr()} -> id={id}, title={title}, company={company} -> input length={len(markdown)}'), end='')
                    result = self.match(f'# {title} \n {markdown}')
                    print(f' -> Result: {cyan(json.dumps(result))}', end='')
                    self._save_result(repo, id, result)
                except (Exception, KeyboardInterrupt) as ex:
                    self._save_error(repo, id, title, company, ex)
                self.totalCount += 1
                self.stopWatch.end()
            self._print_footer(total, idx)
            printHR(yellow)
            return total-idx

    def _load_cv_content(self) -> bool:
        if self._cv_content:
            return True
        if self._cv_loader.load_cv_content():
            self._cv_content = self._cv_loader.get_content()
            self._cv_embedding = self._model.encode([self._cv_content])
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
        except Exception as e:
            print(red(f"Error in fast match: {e}"))
            traceback.print_exc()
            return {"cv_match_percentage": 0}

    def _save_result(self, repo: AiEnrichRepository, id, result: dict):
        repo.update_cv_match(id, result.get('cv_match_percentage'))

    def _save_error(self, repo: AiEnrichRepository, id, title, company, ex):
        print(red(traceback.format_exc()))
        self.jobErrors.add((id, f'{title} - {company}: {ex}'))
        repo.update_enrichment_error(id, str(ex), False)
        print(yellow(f"cv_match_percentage set to -1 (error), id={id}"))

    def _print_footer(self, total, idx):
        print(yellow(f'Processed jobs this run: {idx+1}/{total}, total processed jobs: {self.totalCount}'), end=' ')
        if self.jobErrors:
            print(red(f'Total job errors: {len(self.jobErrors)}'), end=' ')

import json
import traceback
import pandas as pd
import pdfplumber
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from commonlib.mysqlUtil import MysqlUtil
from commonlib.stopWatch import StopWatch
from commonlib.terminalColor import yellow, red, cyan, green, printHR
from commonlib.environmentUtil import getEnv, getEnvBool
from commonlib.stringUtil import removeExtraEmptyLines
from commonlib.dateUtil import getDatetimeNowStr
from commonlib.sqlUtil import emptyToNone, maxLen, updateFieldsQuery

CV_LOCATION = './cv/cv.txt'

QRY_FROM = """
FROM jobs
WHERE cv_match_percentage is null and not (ignored or discarded or closed)
ORDER BY created desc"""
QRY_COUNT = f"""SELECT count(id) {QRY_FROM}"""
QRY_FIND_IDS = f"""SELECT id {QRY_FROM} LIMIT {getEnv('AI_CV_MATCH_NEW_LIMIT', '100')}"""
QRY_FIND = f"""
SELECT id, title, markdown, company
FROM jobs
WHERE id=%s and cv_match_percentage is null and not (ignored or discarded or closed)
ORDER BY created desc 
"""
QRY_UPDATE = """UPDATE jobs SET cv_match_percentage=%s WHERE id=%s"""


class FastCVMatcher:
    _instance = None
    _model = None
    _cv_embedding = None
    _cv_content = None
    
    stopWatch = StopWatch()
    totalCount = 0
    jobErrors = set()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FastCVMatcher, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        print(yellow("Loading embedding model (this may take a while significantly on first run)..."))
        self._model = SentenceTransformer('all-MiniLM-L6-v2') 
        print(cyan("Embedding model loaded."))

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
            total = mysql.count(QRY_COUNT)
            if total == 0:
                return total
            print()
            job_ids = [row[0] for row in mysql.fetchAll(QRY_FIND_IDS)]
            print(yellow(f'{job_ids}'))
            for idx, id in enumerate(job_ids):
                self.stopWatch.start()
                try:
                    job = mysql.fetchOne(QRY_FIND, id)
                    if job is None:
                        continue
                    title = job[1]
                    company = job[3]
                    markdown = removeExtraEmptyLines(job[2].decode("utf-8"))
                    print(green(f'AI CV match job {idx+1}/{total} - {getDatetimeNowStr()} -> id={id}, title={title}, company={company} -> input length={len(markdown)}'), end='')
                    result = self.match(f'# {title} \n {markdown}')
                    print(f' -> Result: {cyan(json.dumps(result))}', end='')
                    self._save_result(mysql, id, result)
                except (Exception, KeyboardInterrupt) as ex:
                    self._save_error(mysql, id, title, company, ex)
                self.totalCount += 1
                self.stopWatch.end()
            self._print_footer(total, idx)
            printHR(yellow)
            return total-idx

    def _load_cv_content(self) -> bool:
        if self._cv_content:
            return True
        if not getEnvBool('AI_CV_MATCH'):
            print(yellow('AI_CV_MATCH disabled'))
            return False
        print(yellow(f'Loading CV from: {CV_LOCATION}'))
        try:
            filePath = Path(CV_LOCATION)
            cvLocationTxt = CV_LOCATION.replace('.pdf', '.txt')
            filePathTxt = Path(cvLocationTxt)
            if not filePath.exists() and not filePathTxt.exists():
                print(red(f'CV file not found: {CV_LOCATION}'))
                return False
            if filePath.suffix.lower() == '.pdf' and not filePathTxt.exists():
                self._cv_content = self._extract_text_from_pdf(CV_LOCATION)
                print(yellow(f'CV (PDF) loaded from: {CV_LOCATION} ({len(self._cv_content)} chars)'))
                with open(cvLocationTxt, 'w', encoding='utf-8') as mdFile:
                    mdFile.write(self._cv_content)
            elif filePathTxt.exists():
                with open(cvLocationTxt, 'r', encoding='utf-8') as f:
                    self._cv_content = f.read()
                print(yellow(f'CV (text from PDF) loaded from: {cvLocationTxt} ({len(self._cv_content)} chars)'))
            else:
                print(red(f'Unsupported CV file format'))
                return False
            if not self._cv_content or not self._cv_content.strip():
                print(red('CV file is empty'))
                return False
            self._cv_embedding = self._model.encode([self._cv_content])
            return True
        except Exception:
            print(red(f'Error loading CV:'))
            print(red(traceback.format_exc()))
            return False

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        all_text = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text: all_text.append(text)
                for table in page.extract_tables():
                    df = pd.DataFrame(table[1:], columns=table[0])
                    all_text.append(df.to_markdown(index=False))
        return "\n\n".join(all_text)

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

    def _save_result(self, mysql: MysqlUtil, id, result: dict):
        cv_match = result.get('cv_match_percentage')
        params = maxLen(emptyToNone((cv_match, id)), (None, None))
        mysql.updateFromAI(QRY_UPDATE, params)

    def _save_error(self, mysql: MysqlUtil, id, title, company, ex):
        print(red(traceback.format_exc()))
        self.jobErrors.add((id, f'{title} - {company}: {ex}'))
        # Using a fixed error length limit here
        aiEnrichError = str(ex)[:500] 
        # Note: We are setting cv_match_percentage to -1 on error
        query, params = updateFieldsQuery([id], {'cv_match_percentage': -1})
        mysql.executeAndCommit(query, params)
        print(yellow(f"cv_match_percentage set to -1 (error), id={id}"))

    def _print_footer(self, total, idx):
        print(yellow(f'Processed jobs this run: {idx+1}/{total}, total processed jobs: {self.totalCount}'), end=' ')
        if self.jobErrors:
            print(red(f'Total job errors: {len(self.jobErrors)}'), end=' ')

import re
from typing import Tuple
from commonlib.mysqlUtil import QRY_FIND_JOB_BY_JOB_ID, MysqlUtil
from commonlib.mergeDuplicates import getSelect, mergeDuplicatedJobs
from commonlib.terminalColor import green, yellow
from ..core.baseScrapper import htmlToMarkdown, validate, debug
from ..util.persistence_manager import PersistenceManager


class IndeedService:
    def __init__(self, mysql: MysqlUtil, persistence_manager: PersistenceManager):
        self.mysql = mysql
        self.persistence_manager = persistence_manager
        self.web_page = "Indeed"
        self.debug = True

    def set_debug(self, debug: bool):
        self.debug = debug

    def get_job_id(self, url: str):
        # Extract job ID from Indeed URL
        import urllib.parse
        import hashlib

        # If URL is already clean, extract the job ID
        if url.startswith("https://es.indeed.com/viewjob?jk="):
            return url.replace("https://es.indeed.com/viewjob?jk=", "").split("&")[0]
        if url.startswith("https://es.indeed.com/viewjob?vjk="):
            return url.replace("https://es.indeed.com/viewjob?vjk=", "").split("&")[0]

        # Parse the URL and extract query parameters
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # Try to get 'jk' parameter directly
        if "jk" in query_params and query_params["jk"]:
            return query_params["jk"][0]

        # Try to get 'vjk' parameter directly
        if "vjk" in query_params and query_params["vjk"]:
            return query_params["vjk"][0]

        # If no jk parameter, try regex extraction as fallback
        match = re.search(r"[?&]jk=([^&]+)", url)
        if match:
            return match.group(1)

        match = re.search(r"[?&]vjk=([^&]+)", url)
        if match:
            return match.group(1)

        # For pagead URLs without jk parameter, we need to extract the job ID from the click tracking
        unique_parts = []

        if "xkcb" in query_params and query_params["xkcb"]:
            unique_parts.append(query_params["xkcb"][0])

        if "camk" in query_params and query_params["camk"]:
            unique_parts.append(query_params["camk"][0])

        if unique_parts:
            unique_string = "_".join(unique_parts)
            return hashlib.md5(unique_string.encode()).hexdigest()[:16]

        # Last resort - use hash of the entire URL
        return hashlib.md5(url.encode()).hexdigest()[:16]

    def job_exists_in_db(self, url: str) -> Tuple[str, bool]:
        job_id = self.get_job_id(url)
        return (job_id, self.mysql.fetchOne(QRY_FIND_JOB_BY_JOB_ID, job_id) is not None)

    def process_job(self, title, company, location, url, html, easy_apply):
        try:
            job_id = self.get_job_id(url)
            md = htmlToMarkdown(html)
            md = self.post_process_markdown(md)
            # Use the actual URL from seleniumService.getUrl() directly
            print(f"{job_id}, {title}, {company}, {location}, easy_apply={easy_apply} - ", end="", flush=True)
            # Double check existence with the final canonical ID
            if self.mysql.fetchOne(QRY_FIND_JOB_BY_JOB_ID, job_id) is not None:
                print(yellow(f"Job id={job_id} already exists in DB (late check), IGNORED."), end="", flush=True)
                return True
            if validate(title, url, company, md, self.debug):
                if id := self.mysql.insert((job_id, title, company, location, url, md, easy_apply, self.web_page)):
                    print(green(f"INSERTED {id}!"), end="", flush=True)
                    mergeDuplicatedJobs(self.mysql, getSelect())
                    return True
                else:
                    debug(self.debug, exception=True)
            return False
        except (ValueError, KeyboardInterrupt) as e:
            raise e
        except Exception:
            debug(self.debug, 'xxx', exception=True)
            return False

    def post_process_markdown(self, md):
        txt = re.sub(r"\[([^\]]+)\]\(/ofertas-trabajo[^\)]+\)", r"\1", md)
        txt = re.sub(r"[\\]+-", "-", txt)
        txt = re.sub(r"[\\]+\.", ".", txt)
        txt = re.sub(r"-\n", "\n", txt)
        txt = re.sub(r"(\n[  ]*){3,}", "\n\n", txt)
        txt = re.sub(r"[-*] #", "#", txt)
        return txt

    def update_state(self, keyword: str, page: int):
        if self.persistence_manager:
            self.persistence_manager.update_state(self.web_page, keyword, page)

    def should_skip_keyword(self, keyword: str) -> Tuple[bool, int]:
        saved_state = {}
        if self.persistence_manager:
            saved_state = self.persistence_manager.get_state(self.web_page)
        saved_keyword = saved_state.get("keyword")
        saved_page = saved_state.get("page", 1)
        if saved_keyword and saved_keyword == keyword:
            return False, saved_page
        if saved_keyword:
            # If we have a saved keyword but it is not this one, we might need to skip
            # But the logic in indeed.py loop was:
            # for keywords in JOBS_SEARCH.split(','):
            #     if saved_keyword:
            #         if saved_keyword == current_keyword: skip = False
            #         elif skip: continue
            # This implies simpler checking at call site or specialized method here.
            # I will keep it simple here and let the caller handle the loop logic
            # OR I can replicate the logic:
            pass
        return False, 1

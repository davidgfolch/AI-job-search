import re
import urllib.parse
import hashlib
from typing import Tuple
from commonlib.mysqlUtil import QRY_FIND_JOB_BY_JOB_ID, MysqlUtil
from commonlib.mergeDuplicates import getSelect, mergeDuplicatedJobs
from commonlib.terminalColor import green, yellow
from ..core.baseScrapper import htmlToMarkdown, validate, debug, removeUrlParameter
from ..util.persistence_manager import PersistenceManager
from .BaseService import BaseService


class IndeedService(BaseService):
    def __init__(self, mysql: MysqlUtil, persistence_manager: PersistenceManager):
        super().__init__(mysql, persistence_manager, "Indeed")
        self.debug = True

    def get_job_id(self, url: str):
        # Extract job ID from Indeed URL

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

    def process_job(self, title, company, location, url, html, easy_apply):
        try:
            url = removeUrlParameter(url, 'cf-turnstile-response')
            job_id = self.get_job_id(url)
            md = htmlToMarkdown(html)
            md = self.post_process_markdown(md)
            # Use the actual URL from seleniumService.getUrl() directly
            print(f"{job_id}, {title}, {company}, easy_apply={easy_apply} - ", end="", flush=True)
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

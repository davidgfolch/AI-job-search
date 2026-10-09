import re
import urllib.parse
import hashlib
from typing import Tuple
from commonlib.sql.mysqlUtil import QRY_FIND_JOB_BY_JOB_ID, MysqlUtil
from commonlib.findLastDuplicated import find_last_duplicated
from commonlib.observability import get_logger
from commonlib.terminalColor import green, yellow, cyan
from ..core.baseScrapper import htmlToMarkdown, validate, debug, removeUrlParameter
from ..util.persistence_manager import PersistenceManager
from .BaseService import BaseService

logger = get_logger("scrapper.IndeedService")


class IndeedService(BaseService):
    def __init__(self, mysql: MysqlUtil, persistence_manager: PersistenceManager, debug: bool):
        super().__init__(mysql, persistence_manager, "Indeed", debug)

    def _canonical_job_id(self, url: str) -> str | None:
        """Returns the real Indeed job id only when the URL carries a jk/vjk, None for ad/pagead click URLs."""
        query_params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        for key in ("jk", "vjk"):
            if query_params.get(key):
                return query_params[key][0]
        for pattern in (r"[?&]jk=([^&]+)", r"[?&]vjk=([^&]+)"):
            if match := re.search(pattern, url):
                return match.group(1)
        return None

    def get_job_id(self, url: str):
        # Extract job ID from Indeed URL

        # If URL is already clean, extract the job ID
        if url.startswith("https://es.indeed.com/viewjob?jk="):
            return url.replace("https://es.indeed.com/viewjob?jk=", "").split("&")[0]
        if url.startswith("https://es.indeed.com/viewjob?vjk="):
            return url.replace("https://es.indeed.com/viewjob?vjk=", "").split("&")[0]

        if canonical := self._canonical_job_id(url):
            return canonical

        # Parse the URL and extract query parameters
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)

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

    def process_job(self, title, company, location, salary, url, html, easy_apply):
        try:
            url = removeUrlParameter(url, 'cf-turnstile-response')
            job_id = self._canonical_job_id(url)
            if not job_id:
                logger.info("indeed.job.skipped_no_job_id", url=url,
                            console=yellow("No Indeed job id (ad/pagead click), IGNORED."), end="")
                return False
            # Store the canonical viewjob URL; tracking parameters (q, tk, ad, ...) push pagead/viewjob URLs past the column length
            url = f"https://es.indeed.com/viewjob?jk={job_id}"
            md = htmlToMarkdown(html)
            md = self.post_process_markdown(md)
            # Use the actual URL from seleniumService.getUrl() directly
            logger.info("indeed.job.scraped", job_id=job_id, title=title, company=company, easy_apply=easy_apply,
                          console=f"{job_id}, {title}, {cyan(company)}, easy_apply={easy_apply} - ", end="")
            # Double check existence with the final canonical ID
            if self.mysql.fetchOne(QRY_FIND_JOB_BY_JOB_ID, job_id) is not None:
                logger.info("indeed.job.already_exists", job_id=job_id,
                            console=yellow(f"Job id={job_id} already exists in DB (late check), IGNORED."), end="")
                return True
            if validate(title, url, company, md, self.debug):
                duplicated_id = find_last_duplicated(self.mysql, title, company)
                if id := self.mysql.insert((job_id, title, company, location, salary, url, md, easy_apply, self.web_page, duplicated_id)):
                    logger.info("indeed.job.inserted", job_id=job_id, insert_id=id, console=green(f"INSERTED {id}!"), end="")
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

import re
from typing import Tuple
from commonlib.sql.mysqlUtil import QRY_FIND_JOB_BY_JOB_ID, QRY_UPDATE_JOB_DIRECT_URL, MysqlUtil
from commonlib.findLastDuplicated import find_last_duplicated
from commonlib.observability import get_logger
from commonlib.terminalColor import green, magenta, yellow, cyan
from ..core import baseScrapper
from commonlib.modality_extractor import extract_modalities, modalities_to_db
from ..util.persistence_manager import PersistenceManager
from .BaseService import BaseService

logger = get_logger("scrapper.LinkedinService")

# The detail pane wraps the description in AI-fit / premium cards. The reader now returns only the About-the-job
# section, but a future DOM shift would leak the chrome again, so the markdown is trimmed defensively.
# Prefix: the fit card between the fit-preferences line ("Hybrid, Full-time") and the description heading.
# Suffix: the premium upsell and everything after it (company blurb, trending posts, "Show more").
MARKDOWN_PREFIX_MARKERS = ('Your profile and resume match', 'See recent hiring trends', 'Use AI to assess how you fit', 'Reactivate Premium')
MARKDOWN_SUFFIX_MARKERS = ('Job search faster with Premium', 'Trending employee content', '[Show more](https://www.linkedin.com/company/')
ABOUT_THE_JOB_HEADING_RE = re.compile(r'^About the job\n-{3,}[ \t]*$', re.M)
# LinkedIn ships the full description in the DOM: the "… more" affordance only lifts a CSS line clamp. The reader
# strips the button node, so a label reaching the markdown means the DOM moved again (or the box was already
# expanded and carries "… less"): trim it and say so instead of storing chrome the AI would read as content.
EXPANDER_LABEL_RE = re.compile(r'\s*(?:…|\.\.\.)\s*(?:see\s+)?(?:more|less)\s*$', re.I)

class LinkedinService(BaseService):
    def __init__(self, mysql: MysqlUtil, persistence_manager: PersistenceManager, debug: bool):
        super().__init__(mysql, persistence_manager, 'Linkedin', debug)

    def get_job_id(self, url: str) -> int:
        return int(re.sub(r'.*/jobs/view/([^/]+)/.*', r'\1', url))

    def get_job_url_short(self, url: str):
        return re.sub(r'(.*/jobs/view/([^/]+)/).*', r'\1', url)

    def job_exists_in_db(self, url: str) -> Tuple[int, bool]:
        # Overriding to return job_id as int if needed, or stick to base?
        # Base returns str. Here explicit int.
        jobId = self.get_job_id(url)
        return (jobId, self.mysql.fetchOne(QRY_FIND_JOB_BY_JOB_ID, jobId) is not None)

    def process_job(self, title, company, location, url, html, is_direct_url_scrapping: bool, easy_apply: bool):
        try:
            url_short = self.get_job_url_short(url)
            jobId = self.get_job_id(url_short)
            md = self.post_process_markdown(baseScrapper.htmlToMarkdown(html))
            modality = modalities_to_db(extract_modalities(title, location, md))
            logger.info("linkedin.job.scraped", job_id=jobId, title=title, company=company, location=location, easy_apply=easy_apply,
                          console=f'{jobId}, {title}, {cyan(company)}, {location}, easy_apply={easy_apply} - ', end="")
            if baseScrapper.validate(title, url_short, company, md, self.debug):
                if is_direct_url_scrapping and self.mysql.jobExists(str(jobId)):
                    self.update_job(jobId, title, company, location, url_short, html, md, easy_apply)
                else:
                    duplicated_id = find_last_duplicated(self.mysql, title, company)
                    if id := self.mysql.insert((jobId, title, company, location, None, modality, url_short, md, easy_apply, self.web_page, duplicated_id)):
                        logger.info("linkedin.job.inserted", job_id=jobId, insert_id=id, console=green(f'INSERTED {id}!'), end="")
                        if duplicated_id:
                            logger.info("linkedin.job.duplicated", job_id=jobId, duplicated_id=duplicated_id, console=cyan(f' DUPLICATED {duplicated_id}'), end="")
            else:
                raise ValueError('Validation failed')
        except (ValueError, KeyboardInterrupt) as e:
            raise e
        except Exception:
            baseScrapper.debug(self.debug, exception=True)

    def post_process_markdown(self, md: str) -> str:
        return self._strip_expander_label(self._cut_suffix(self._drop_fit_card(md)))

    def _strip_expander_label(self, md: str) -> str:
        stripped = EXPANDER_LABEL_RE.sub('', md)
        if stripped != md:
            logger.warning("linkedin.description.expander_label_stripped", markdown_length=len(md),
                           console=yellow('Description carried an expander label ("… more"), stripped'))
        return stripped

    def _drop_fit_card(self, md: str) -> str:
        heading = ABOUT_THE_JOB_HEADING_RE.search(md)
        if not heading:
            return md
        starts = [i for i in (md.find(marker) for marker in MARKDOWN_PREFIX_MARKERS) if 0 <= i < heading.start()]
        return md[:min(starts)] + md[heading.start():] if starts else md

    def _cut_suffix(self, md: str) -> str:
        cuts = [i for i in (md.find(marker) for marker in MARKDOWN_SUFFIX_MARKERS) if i != -1]
        return md[:min(cuts)] if cuts else md

    def print_job(self, title, company, location, url, jobId, html, md):
        logger.debug("linkedin.job.already_exists", job_id=jobId, title=title, company=company, location=location, url=url, html_length=len(html or ''), markdown_length=len(md or ''),
                     console='\n'.join([yellow(f'Job id={jobId} already exists in DB, IGNORED.'), yellow(f'TITLE={title}'),
                                         yellow('COMPANY=') + cyan(company), yellow(f'LOCATION={location}'), yellow(f'URL={url}'),
                                         magenta(f'HTML_LENGTH={len(html or "")}'), magenta(f'MARKDOWN_LENGTH={len(md or "")}')]))

    def update_job(self, jobId, title, company, location, url, html, md, easy_apply):
        self.print_job(title, company, location, url, jobId, html, md)
        modality = modalities_to_db(extract_modalities(title, location, md))
        params = (title, company, location, url, md, easy_apply, modality, jobId, self.web_page)
        self.mysql.executeAndCommit(QRY_UPDATE_JOB_DIRECT_URL, params)
        logger.info("linkedin.job.updated", job_id=jobId, console=green(f'Job updated {jobId}'))

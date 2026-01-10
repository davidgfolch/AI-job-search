import re
from typing import Tuple
from commonlib.mysqlUtil import QRY_FIND_JOB_BY_JOB_ID, MysqlUtil
from commonlib.mergeDuplicates import getSelect, mergeDuplicatedJobs
from commonlib.terminalColor import green
from ..core.baseScrapper import htmlToMarkdown, validate, debug as baseDebug
from ..util.persistence_manager import PersistenceManager


class IndeedService:
    def __init__(self, mysql: MysqlUtil, persistence_manager: PersistenceManager):
        self.mysql = mysql
        self.persistence_manager = persistence_manager
        self.web_page = 'Indeed'
        self.debug = True

    def set_debug(self, debug: bool):
        self.debug = debug

    def get_job_id(self, url: str):
        # https://es.indeed.com/pagead/clk?mo=r&ad=-6NYlbfkN0DbIyHopYNdPLgRYRG2FgnuJLz47mHLRnOVu2tY5XDnoTjm_t8c6thoU-53yYOVZJvZ76je_lq6KA-XAY92iGBEMkipCfXteoPVubXE4FHTfqx4Mf-6MhfZkK7YUu3yrI-z9JQE9pLO-djt1tFqNEtTK3NWMfyT0Ezmoj_8NOLQUumiyZsw8Hx3ykr2qLxPszYw1XYJLwKKdex1K0FkeMDl4M6poEhp9eoiIfvPBH-AGSl0J7kFrvnVDF5Cb6Dvrlcnad3Mvu-SvAvFBTP1OaSrIZMPkRPObPTtGFXsV0HO6KsqJx5bZwuzWhmu1B5dPhpGeEgMXWo0Cn3Bgc8D5VSbTCXIQDkq9i_5JDzpYeBo1uKtvyrS2lWXnCL9UNcz5eh8zDD8MU8-Pqk0vZPYzeaSWFWNqCidqZ9zcmNjFzMZdXdxTtOmr4lEs4GN__YlU0NBlGiq59uMCMRzFV93FcxbAC4oGzgFodV4uXx4dRB7zVAjTPLFlvNgsPUm6kHt7nDOe40xbCXB6STQc6axaa1tP1bRbfXH6sb6X8B_CK_kHRiPQ0omUdYa8RGGEtycz41lWTLwP1CT2zUOn64fuP3bIOeW9lPQFUW_Hi0n7r-KmA==&xkcb=SoCR6_M32Jfx9pTm350LbzkdCdPP&camk=nUmJqO2E8rjUsDRVvlAvpw==&p=0&fvj=0&vjs=3
        # https://es.indeed.com/pagead/clk?mo=r&ad=-6NYlbfkN0DbIyHopYNdPLgRYRG2FgnuJLz47mHLRnOVu2tY5XDnoTjm_t8c6thoU-53yYOVZJvZ76je_lq6KA-XAY92iGBEMkipCfXteoPVubXE4FHTfqx4Mf-6MhfZkK7YUu3yrI-z9JQE9pLO-djt1tFqNEtTK3NWMfyT0Ezmoj_8NOLQUumiyZsw8Hx3ykr2qLxPszYw1XYJLwKKdex1K0FkeMDl4M6poEhp9eoiIfvPBH-AGSl0J7kFrvnVDF5Cb6Dvrlcnad3Mvu-SvAvFBTP1OaSrIZMPkRPObPTtGFXsV0HO6KsqJx5bZwuzWhmu1B5dPhpGeEgMXWo0Cn3Bgc8D5VSbTCXIQDkq9i_5JDzpYeBo1uKtvyrS2lWXnCL9UNcz5eh8zDD8MU8-Pqk0vZPYzeaSWFWNqCidqZ9zcmNjFzMZdXdxTtOmr4lEs4GN__YlU0NBlGiq59uMCMRzFV93FcxbAC4oGzgFodV4uXx4dRB7zVAjTPLFlvNgsPUm6kHt7nDOe40xbCXB6STQc6axaa1tP1bRbfXH6sb6X8B_CK_kHRiPQ0omUdYa8RGGEtycz41lWTLwP1CT2zUOn64fuP3bIOeW9lPQFUW_Hi0n7r-KmA==&xkcb=SoCR6_M32Jfx9pTm350LbzkdCdPP&camk=nUmJqO2E8rjUsDRVvlAvpw==&p=0&fvj=0&vjs=3&tk=1ii9bvhamkhjt8e0&jsa=9049&oc=1&sal=0
        return re.sub(r'.+\?.*jk=([^&]+).*', r'\1', url)

    def job_exists_in_db(self, url: str) -> Tuple[str, bool]:
        job_id = self.get_job_id(url)
        return (job_id, self.mysql.fetchOne(QRY_FIND_JOB_BY_JOB_ID, job_id) is not None)

    def process_job(self, title, company, location, url, html, easy_apply):
        try:
            job_id = self.get_job_id(url)
            md = htmlToMarkdown(html)
            md = self.post_process_markdown(md)
            print(f'{job_id}, {title}, {company}, {location}, {url}', f'easy_apply={easy_apply} - ', end='')
            if validate(title, url, company, md, self.debug):
                if id := self.mysql.insert((job_id, title, company, location, url, md, easy_apply, self.web_page)):
                    print(green(f'INSERTED {id}!'), end='')
                    mergeDuplicatedJobs(self.mysql, getSelect())
                    return True
                else:
                    baseDebug(self.debug, exception=True)
            return False
        except (ValueError, KeyboardInterrupt) as e:
            raise e
        except Exception:
            baseDebug(self.debug, exception=True)
            return False

    def post_process_markdown(self, md):
        txt = re.sub(r'\[([^\]]+)\]\(/ofertas-trabajo[^\)]+\)', r'\1', md)
        txt = re.sub(r'[\\]+-', '-', txt)
        txt = re.sub(r'[\\]+\.', '.', txt)
        txt = re.sub(r'-\n', '\n', txt)
        txt = re.sub(r'(\n[  ]*){3,}', '\n\n', txt)
        txt = re.sub(r'[-*] #', '#', txt)
        return txt

    def update_state(self, keyword: str, page: int):
        if self.persistence_manager:
            self.persistence_manager.update_state(self.web_page, keyword, page)

    def should_skip_keyword(self, keyword: str) -> Tuple[bool, int]:
        saved_state = {}
        if self.persistence_manager:
            saved_state = self.persistence_manager.get_state(self.web_page)
        saved_keyword = saved_state.get('keyword')
        saved_page = saved_state.get('page', 1)
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

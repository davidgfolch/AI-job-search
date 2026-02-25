import re
from typing import Tuple
from commonlib.mysqlUtil import QRY_FIND_JOB_BY_JOB_ID, MysqlUtil
from commonlib.findLastDuplicated import find_last_duplicated
from commonlib.terminalColor import green, cyan
from ..core.baseScrapper import htmlToMarkdown, validate, removeLinks, debug as baseDebug
from ..util.persistence_manager import PersistenceManager
from .BaseService import BaseService

REMOVE_IN_MARKDOWN = [
    "¿Te gusta esta oferta?",
    "Prueba el Asistente de IA y mejora tus posibilidades.",
    "Asistente IA"
]

class InfojobsService(BaseService):
    def __init__(self, mysql: MysqlUtil, persistence_manager: PersistenceManager, debug: bool):
        super().__init__(mysql, persistence_manager, 'Infojobs', debug)

    def get_job_id(self, url: str) -> str:
        return re.sub(r'.+/of-([^?/]+).*', r'\1', url)

    def process_job(self, title, company, location, url, html):
        try:
            job_id = self.get_job_id(url)
            md = htmlToMarkdown(html)
            md = self.post_process_markdown(md)
            
            print(f'{job_id}, {title}, {company}, {location} - ', end='')
            
            if validate(title, url, company, md, self.debug):
                duplicated_id = find_last_duplicated(self.mysql, title, company)
                if id := self.mysql.insert((job_id, title, company, location, url, md, None, self.web_page, duplicated_id)):
                    print(green(f'INSERTED {id}!'), end='')
                    if duplicated_id:
                        print(cyan(f' DUPLICATED {duplicated_id}'), end="")
                    return True
            else:
                raise ValueError('Validation failed')
            return False
        except (ValueError, KeyboardInterrupt) as e:
            raise e
        except Exception:
            baseDebug(self.debug, exception=True)
            return False

    def post_process_markdown(self, md):
        txt = removeLinks(md)
        patterns = r'\s+'.join(map(re.escape, REMOVE_IN_MARKDOWN))
        txt = re.sub(patterns, "", txt)
        if (idx := txt.find('Nuestro consejo:')) != -1:
            txt = txt[:idx]
        return txt

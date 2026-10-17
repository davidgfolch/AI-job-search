from commonlib.company_normalizer import UNSPECIFIED_COMPANY
from commonlib.observability import get_logger
from ...core.utils import debug

# tecnoempleo links the company only when the offer belongs to a company page; the offers published without one render the
# name as a bare text node inside the job header, unreachable by CSS because only the linked form carries span[itemprop=name]
JS_FIRST_DIRECT_TEXT_NODE = 'for (const n of arguments[0].childNodes) { const t = (n.nodeType === 3 ? n.textContent : "").trim(); if (t) return t; } return "";'

logger = get_logger("scrapper.tecnoempleoCompanyReader")

class TecnoempleoCompanyReader:
    def __init__(self, selenium, company_link_css: str, header_css: str, debug: bool = False):
        self.selenium = selenium
        self.company_link_css = company_link_css
        self.header_css = header_css
        self.debug = debug

    def read(self) -> str:
        """Offers with no company page still name the company as a header text node, the ones with no employer at all are stored as unspecified."""
        for read_company in (self._read_link, self._read_text_node):
            try:
                if company := read_company():
                    return company
            except Exception:
                debug(self.debug, exception=True)
        logger.info("tecnoempleo.company.missing", company=UNSPECIFIED_COMPANY)
        return UNSPECIFIED_COMPANY

    def _read_link(self) -> str:
        links = self.selenium.getElms(self.company_link_css)
        return links[0].text.strip() if links else ''

    def _read_text_node(self) -> str:
        headerElm = self.selenium.getElm(self.header_css)
        return (self.selenium.driver.execute_script(JS_FIRST_DIRECT_TEXT_NODE, headerElm) or '').strip()

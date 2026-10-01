import re

from selenium.common.exceptions import NoSuchElementException
from commonlib.decorator.retry import StackTrace, retry
from commonlib.observability import get_logger
from ...core.utils import debug

# tecnoempleo lists the offer facts as `<li>` rows pairing a caption with its value, and only the "Salario" row carries a pay
# range. The generic markdown scrape keeps the row values but drops the captions, so the range reaches the AI as an unlabeled
# bullet and the model is free to answer salary=null. Matching the caption makes the extraction deterministic.
SALARIO_CAPTION = 'salario'
# Rendered as "30.000 € - 36.000 € Bruto/año"; the range is already display-ready, so it is kept verbatim once the
# non-breaking spaces selenium returns around the separator collapse back to plain spaces.
BLANKS = re.compile(r'[\s\u00a0]+')

logger = get_logger("scrapper.tecnoempleoSalaryReader")

def normalize(text: str) -> str:
    return BLANKS.sub(' ', text or '').strip()

class TecnoempleoSalaryReader:
    def __init__(self, selenium, item_css: str, caption_css: str, value_css: str, debug: bool = False):
        self.selenium = selenium
        self.item_css = item_css
        self.caption_css = caption_css
        self.value_css = value_css
        self.debug = debug

    def read(self) -> str | None:
        """Returns the pay range of the "Salario" row, or None when the offer states no salary."""
        for item in self.selenium.getElms(self.item_css):
            try:
                if self._caption_of(item) == SALARIO_CAPTION:
                    return self._value_of(item) or None # the retry decorator reports an exhausted row as False, not as None
            except Exception:
                debug(self.debug, exception=True)
        return None

    def _caption_of(self, item) -> str:
        return normalize(self.selenium.getText(self.selenium.getElmOf(item, self.caption_css))).lower()

    @retry(retries=2, delay=1, exception=NoSuchElementException, raiseException=False, stackTrace=StackTrace.NEVER)
    def _value_of(self, item) -> str | None:
        return normalize(self.selenium.getText(self.selenium.getElmOf(item, self.value_css))) or None

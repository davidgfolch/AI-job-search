import pytest
from unittest.mock import MagicMock
from selenium.common.exceptions import NoSuchElementException
from scrapper.navigator.components.tecnoempleoSalaryReader import TecnoempleoSalaryReader

ITEM_CSS, CAPTION_CSS, VALUE_CSS = 'li', 'span.caption', 'span.value'

class TestTecnoempleoSalaryReader:
    @pytest.fixture
    def selenium(self):
        return MagicMock()

    @pytest.fixture
    def reader(self, selenium):
        return TecnoempleoSalaryReader(selenium, ITEM_CSS, CAPTION_CSS, VALUE_CSS, False)

    def _rows(self, selenium, rows):
        """Each <li> resolves its own caption/value spans, so a row missing one raises just for itself"""
        contents = {}
        items = []
        for caption, value in rows:
            item = MagicMock()
            caption_elm = MagicMock(text=caption) if caption is not None else None
            contents[item] = {CAPTION_CSS: caption_elm, VALUE_CSS: value}
            items.append(item)
        def getElms(css, driverOverride=None):
            if css == ITEM_CSS:
                return items
            if css == CAPTION_CSS:
                caption_elm = contents[driverOverride][CAPTION_CSS]
                return [caption_elm] if caption_elm is not None else []
            raise AssertionError(f"unexpected selector {css}")
        selenium.getElms.side_effect = getElms
        def getElmOf(elm, css):
            if contents[elm][css] is None:
                raise NoSuchElementException(f"no {css}")
            return contents[elm][css]
        selenium.getElmOf.side_effect = getElmOf
        selenium.getText.side_effect = lambda elm: elm
        return items

    @pytest.mark.parametrize("rows, expected", [
        ([("Salario", "30.000 € - 36.000 € Bruto/año")], "30.000 € - 36.000 € Bruto/año"),
        ([("Jornada", "Jornada completa"), ("Experiencia", "3 años"), ("Salario", "33.000 € - 42.000 € Bruto/año")], "33.000 € - 42.000 € Bruto/año"),
        ([("salario", "27.000 € - 30.000 € Bruto/año")], "27.000 € - 30.000 € Bruto/año"),
        ([("Salario", "  30.000 € - 36.000 € Bruto/año  ")], "30.000 € - 36.000 € Bruto/año"),
        ([("Salario", "30.000 €\u00a0-\u00a036.000 € Bruto/año")], "30.000 € - 36.000 € Bruto/año"),
        ([("Ubicación", "España"), ("Tipo contrato", "Indefinido")], None),
        ([], None),
    ])
    def test_read(self, reader, selenium, rows, expected):
        self._rows(selenium, rows)
        assert reader.read() == expected

    def test_read_returns_none_when_salary_row_has_no_value(self, reader, selenium):
        self._rows(selenium, [("Salario", None)])
        assert reader.read() is None

    def test_read_skips_a_row_that_cannot_be_read(self, reader, selenium):
        self._rows(selenium, [(None, None), ("Salario", "30.000 € - 36.000 € Bruto/año")])
        assert reader.read() == "30.000 € - 36.000 € Bruto/año"

    def test_read_returns_none_when_every_row_fails(self, reader, selenium):
        self._rows(selenium, [(None, None)])
        assert reader.read() is None

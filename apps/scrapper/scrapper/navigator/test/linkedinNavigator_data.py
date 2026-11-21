from unittest.mock import MagicMock
from scrapper.navigator.linkedinNavigator import CSS_SEL_LOGIN_BUTTON, CSS_SEL_LOGIN_BUTTON_LEGACY

LOGIN_SUBMIT_CASES = [
    ([MagicMock()], [], CSS_SEL_LOGIN_BUTTON_LEGACY),  # old linkedin markup
    ([], [MagicMock()], CSS_SEL_LOGIN_BUTTON),  # current markup, submit is the last button of the last form copy
]

CHECK_RESULTS_CASES = [
    ('99+ results', False, True),
    ('12 results', False, True),
    ('0 results', False, False),  # empty searches now render a "0 results" header instead of a banner
    (None, True, True),  # header not rendered yet: the loop retries and fails loudly if the layout changed
]

EASY_APPLY_CASES = [(["yes"], True), ([], False)]

GET_TOTAL_RESULTS_CASES = [
    ('3 resultados', 3),  # exact, Spanish
    ('12 results', 12),  # exact, English
    ('100+ results', 100),  # legacy capped header
    ('Más de 99 resultados', 99),  # new localized "more than" header
    ('Mǭs de 99 resultados', 99),  # mangled capture seen in the production log
    ('More than 99 results', 99),
    ('Plus de 99 résultats', 99),
    ('Mehr als 99 Ergebnisse', 99),
    ('Mais de 99 vagas', 99),
    ('超过99个结果', 99),
    ('Más de 1.000 resultados', 1000),  # grouped thousands, Spanish
    ('More than 1,000 results', 1000),  # grouped thousands, English
    ('Nenhum resultado', False),  # no digits: retries, then the cycle is skipped
]
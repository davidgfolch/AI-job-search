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
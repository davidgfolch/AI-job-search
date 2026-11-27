import sys
import pytest
from unittest.mock import MagicMock, patch
from scrapper.core.baseScrapper import htmlToMarkdown
from scrapper.navigator.components.linkedinDetailReader import (
    LinkedinDetailReader, CSS_SEL_JOB_DETAIL, CSS_SEL_JOB_TITLE_LINK, CSS_SEL_DETAIL_COMPANY, CSS_SEL_JOB_EASY_APPLY, CSS_SEL_JOB_FIT_PREFERENCES,
    CSS_SEL_JOB_DESCRIPTION_LEGACY, CSS_SEL_JOB_DESCRIPTION_BOX, JS_FIND_ABOUT_THE_JOB_SECTION, JS_READ_FIRST_TEXT_BOX, CSS_SEL_DETAIL_COMPANY_FALLBACKS as COMPANY_FALLBACKS,
    MissingJobDetailFields,
)
from selenium.common.exceptions import NoSuchElementException

class TestLinkedinDetailReader:
    @pytest.fixture
    def mock_selenium(self):
        return MagicMock()

    @pytest.fixture
    def reader(self, mock_selenium):
        return LinkedinDetailReader(mock_selenium)

    def test_read(self, reader, mock_selenium):
        mock_selenium.getText.side_effect = ['Title', 'Company', 'Location']
        mock_selenium.getAttr.return_value = 'https://www.linkedin.com/jobs/view/42/'
        mock_selenium.getElms.return_value = []
        mock_selenium.getHtml.return_value = 'job_html'
        assert reader.read() == ('Title', 'Company', 'Location', 'https://www.linkedin.com/jobs/view/42/', 'job_html')
        mock_selenium.waitUntilClickable.assert_called_with(CSS_SEL_JOB_TITLE_LINK)
        mock_selenium.getText.assert_any_call(CSS_SEL_DETAIL_COMPANY)

    def test_read_missing_field_raises(self, reader, mock_selenium):
        mock_selenium.getText.side_effect = ['Title', '', '', '', '', '', '']
        with pytest.raises(MissingJobDetailFields, match='Missing job detail fields'):
            reader.read()

    @pytest.mark.parametrize("first_result", [NoSuchElementException('pane p link'), ''])
    def test_company_falls_back_to_pane_and_public_selectors(self, reader, mock_selenium, first_result):
        mock_selenium.configure_mock(**{'getText.side_effect': ['Title', first_result, NoSuchElementException('pane link'), 'Public Co', 'Loc'], 'getAttr.return_value': 'u', 'getHtml.return_value': 'h'})
        assert reader.read()[1] == 'Public Co' and all(x in ' '.join(COMPANY_FALLBACKS) for x in ('lazy-column', 'artdeco-entity-lockup__subtitle', 'jobs-unified-top-card__company-name', 'topcard__org-name-link'))

    @pytest.mark.parametrize("attr", ['textContent', 'aria-label', 'title'])
    def test_first_text_reads_hidden_node_attribute(self, reader, mock_selenium, attr):
        elm = MagicMock(); elm.get_attribute.side_effect = lambda name: 'Hidden Co' if name == attr else None
        mock_selenium.getText.return_value = ''
        mock_selenium.getElms.return_value = [elm]
        assert reader._first_text('sel') == 'Hidden Co'

    def test_read_location_falls_back_to_wide_p(self, reader, mock_selenium):
        """The compact span carries city/country only, the parent p adds the posting age"""
        mock_selenium.getText.side_effect = ['Title', 'Company', NoSuchElementException('span'), 'Wide, Spain']
        mock_selenium.getAttr.return_value = 'u'
        mock_selenium.getElms.return_value = []
        mock_selenium.getHtml.return_value = 'h'
        assert reader.read()[2] == 'Wide, Spain'

    def test_read_description_falls_back_to_body(self, reader, mock_selenium):
        mock_selenium.getText.side_effect = ['Title', 'Company', 'Location']
        mock_selenium.getAttr.return_value = 'u'
        mock_selenium.getElms.return_value = []
        mock_selenium.getHtml.side_effect = [NoSuchElementException('about the job'), 'body_html']
        assert reader.read()[4] == 'body_html'

    def test_description_uses_anchored_section(self, reader, mock_selenium):
        """The section is found by heading + single expandable-text-box, so the pane chrome never leaks in"""
        mock_selenium.getText.side_effect = ['Title', 'Company', 'Location']
        mock_selenium.getAttr.return_value = 'u'
        mock_selenium.getElms.return_value = []
        mock_selenium.driver.execute_script.side_effect = [None, 'section_html']
        assert reader.read()[4] == 'section_html'
        mock_selenium.getHtml.assert_not_called()

    def test_description_falls_back_to_legacy_container(self, reader, mock_selenium):
        mock_selenium.getText.side_effect = ['Title', 'Company', 'Location']
        mock_selenium.getAttr.return_value = 'u'
        mock_selenium.getElms.return_value = []
        mock_selenium.driver.execute_script.return_value = None
        mock_selenium.getHtml.return_value = 'legacy_html'
        assert reader.read()[4] == 'legacy_html'
        mock_selenium.getHtml.assert_called_with(CSS_SEL_JOB_DESCRIPTION_LEGACY)

    def test_description_last_resort_uses_first_text_box(self, reader, mock_selenium):
        mock_selenium.getText.side_effect = ['Title', 'Company', 'Location']
        mock_selenium.getAttr.return_value = 'u'
        mock_selenium.getElms.return_value = []
        mock_selenium.driver.execute_script.return_value = None
        mock_selenium.getHtml.side_effect = [NoSuchElementException('legacy gone'), 'box_html']
        assert reader.read()[4] == 'box_html'
        mock_selenium.getHtml.assert_called_with(CSS_SEL_JOB_DESCRIPTION_BOX)

    def test_expand_clicks_section_buttons_with_legacy_fallback(self, reader, mock_selenium):
        mock_selenium.driver.execute_script.return_value = None
        reader._expand_description()
        script = mock_selenium.driver.execute_script.call_args.args[0]
        assert 'findSection' in script
        assert 'expandable-text-button' in script
        assert 'JobDetails_AboutTheJob_' in script
        assert 'firstBox' in script  # the box is clicked even when the heading anchor misses

    @pytest.mark.parametrize("result, expected", [(2, 2), (0, 0), (None, 0), (Exception('driver gone'), 0)])
    def test_expand_description_returns_click_count(self, reader, mock_selenium, result, expected):
        if isinstance(result, Exception):
            mock_selenium.driver.execute_script.side_effect = result
        else:
            mock_selenium.driver.execute_script.return_value = result
        assert reader._expand_description() == expected

    @pytest.mark.parametrize("script", ['JS_READ_ABOUT_THE_JOB_SECTION', 'JS_READ_FIRST_TEXT_BOX'])
    def test_read_scripts_strip_the_expander_label(self, script):
        """The '… more' affordance only lifts a CSS clamp: its label must never reach the markdown"""
        source = getattr(sys.modules[LinkedinDetailReader.__module__], script)
        assert 'expandable-text-button' in source
        assert 'remove()' in source

    @pytest.mark.parametrize("script_html, get_html, expected", [
        ('box_html', None, 'box_html'),
        (None, 'legacy_box_html', 'legacy_box_html'),
        (None, NoSuchElementException('no box'), None),
    ])
    def test_box_html_prefers_live_dom_then_falls_back(self, reader, mock_selenium, script_html, get_html, expected):
        mock_selenium.driver.execute_script.return_value = script_html
        if isinstance(get_html, Exception):
            mock_selenium.getHtml.side_effect = get_html
        else:
            mock_selenium.getHtml.return_value = get_html
        assert reader._box_html() == expected
        if get_html is not None:
            mock_selenium.getHtml.assert_called_with(CSS_SEL_JOB_DESCRIPTION_BOX)

    def test_read_without_description_raises(self, reader, mock_selenium):
        mock_selenium.getText.side_effect = ['Title', 'Company', 'Location']
        mock_selenium.getAttr.return_value = 'u'
        mock_selenium.getElms.return_value = []
        mock_selenium.getHtml.side_effect = NoSuchElementException('gone')
        with pytest.raises(NoSuchElementException, match='Job description not found'):
            reader.read()

    def test_read_prepends_fit_preferences(self, reader, mock_selenium):
        mock_selenium.getText.side_effect = ['Title', 'Company', 'Location', 'Remote', 'Full-time']
        mock_selenium.getAttr.return_value = 'u'
        mock_selenium.getElms.return_value = [MagicMock(), MagicMock()]
        mock_selenium.getHtml.return_value = 'job_html'
        assert reader.read()[4] == '<p>Remote, Full-time</p>job_html'
        mock_selenium.getElms.assert_called_with(CSS_SEL_JOB_FIT_PREFERENCES)

    @pytest.mark.parametrize("description_html", [
        'En SEREM buscamos incorporar un/a Full Stack Developer',   # inline text: used to glue onto the preferences
        '<strong>This position</strong> is listed on behalf of a partner company',
        '<p>Desde ISPROX buscamos para uno de nuestros clientes</p>',  # block start: already separated
    ])
    def test_fit_preferences_never_glue_to_the_description(self, reader, mock_selenium, description_html):
        mock_selenium.getText.side_effect = ['Title', 'Company', 'Location', 'Remote', 'Full-time']
        mock_selenium.getAttr.return_value = 'u'
        mock_selenium.getElms.return_value = [MagicMock(), MagicMock()]
        mock_selenium.driver.execute_script.side_effect = [None, description_html]
        assert htmlToMarkdown(reader.read()[4]).startswith('Remote, Full-time\n\n')

    def test_detail_pane_selector_targets_open_job_lazy_column(self):
        """The nth-child path was removed; the pane is the componentkey-bearing lazy-column holding the open job's title link"""
        assert 'data-testid="lazy-column"' in CSS_SEL_JOB_DETAIL
        assert 'componentkey' in CSS_SEL_JOB_DETAIL
        assert ':has(a[href*="/jobs/view/"])' in CSS_SEL_JOB_DETAIL
        assert CSS_SEL_JOB_TITLE_LINK.startswith(CSS_SEL_JOB_DETAIL)

    @pytest.mark.parametrize("source", [JS_FIND_ABOUT_THE_JOB_SECTION, JS_READ_FIRST_TEXT_BOX])
    def test_read_scripts_scope_to_the_detail_pane(self, source):
        assert 'data-testid="lazy-column"' in source and 'componentkey' in source

    def test_heading_anchor_covers_localized_ui(self):
        assert 'acerca del empleo' in JS_FIND_ABOUT_THE_JOB_SECTION

    @pytest.mark.parametrize("href, expected", [
        ('https://www.linkedin.com/jobs/view/4477175173/?trackingId=x', '4477175173'),
        ('https://www.linkedin.com/jobs/view/42/', '42'),
        (None, None),
        ('https://www.linkedin.com/jobs/search/?currentJobId=1', None),
    ])
    def test_job_id(self, reader, mock_selenium, href, expected):
        if href is None:
            mock_selenium.getAttr.side_effect = NoSuchElementException('detail not open')
        else:
            mock_selenium.getAttr.return_value = href
        assert reader.job_id() == expected

    @patch('scrapper.navigator.components.linkedinDetailReader.sleep')
    @pytest.mark.parametrize("hrefs, expected, sleeps", [
        ('42', True, 0), (('41', '42'), True, 1), ('41', False, 2),
    ])
    def test_wait_for_job(self, mock_sleep, reader, mock_selenium, hrefs, expected, sleeps):
        mock_selenium.getAttr.side_effect = [f'https://www.linkedin.com/jobs/view/{h}/' for h in (hrefs if isinstance(hrefs, tuple) else (hrefs,))]
        assert reader.wait_for_job('42', timeout_s=1) is expected
        assert mock_sleep.call_count == sleeps

    @pytest.mark.parametrize("elms, expected", [([MagicMock()], True), ([], False)])
    def test_check_easy_apply(self, reader, mock_selenium, elms, expected):
        mock_selenium.getElms.return_value = elms
        assert reader.check_easy_apply() is expected
        mock_selenium.getElms.assert_called_with(CSS_SEL_JOB_EASY_APPLY)

import pytest
from unittest.mock import MagicMock, patch
from scrapper.navigator.components.linkedinDetailReader import (
    LinkedinDetailReader, CSS_SEL_JOB_TITLE_LINK, CSS_SEL_DETAIL_COMPANY, CSS_SEL_JOB_EASY_APPLY, CSS_SEL_JOB_FIT_PREFERENCES,
    CSS_SEL_JOB_DESCRIPTION_LEGACY, CSS_SEL_JOB_DESCRIPTION_BOX,
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
        mock_selenium.getText.side_effect = ['Title', '', 'Location']
        with pytest.raises(NoSuchElementException, match='Missing job detail fields'):
            reader.read()

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
        assert reader.read()[4] == 'Remote, Full-timejob_html'
        mock_selenium.getElms.assert_called_with(CSS_SEL_JOB_FIT_PREFERENCES)

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
    def test_wait_for_job_matches_immediately(self, mock_sleep, reader, mock_selenium):
        mock_selenium.getAttr.return_value = 'https://www.linkedin.com/jobs/view/42/'
        assert reader.wait_for_job('42') is True
        mock_sleep.assert_not_called()

    @patch('scrapper.navigator.components.linkedinDetailReader.sleep')
    def test_wait_for_job_retries_until_match(self, mock_sleep, reader, mock_selenium):
        mock_selenium.getAttr.side_effect = ['https://www.linkedin.com/jobs/view/41/', 'https://www.linkedin.com/jobs/view/42/']
        assert reader.wait_for_job('42') is True
        assert mock_sleep.call_count == 1

    @patch('scrapper.navigator.components.linkedinDetailReader.sleep')
    def test_wait_for_job_times_out(self, mock_sleep, reader, mock_selenium):
        mock_selenium.getAttr.return_value = 'https://www.linkedin.com/jobs/view/41/'
        assert reader.wait_for_job('42', timeout_s=1) is False
        assert mock_sleep.call_count == 2

    @pytest.mark.parametrize("elms, expected", [([MagicMock()], True), ([], False)])
    def test_check_easy_apply(self, reader, mock_selenium, elms, expected):
        mock_selenium.getElms.return_value = elms
        assert reader.check_easy_apply() is expected
        mock_selenium.getElms.assert_called_with(CSS_SEL_JOB_EASY_APPLY)

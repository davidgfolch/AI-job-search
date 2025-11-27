import sys
from pathlib import Path
import pytest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture(autouse=True)
def mock_sleep():
    """
    Mock sleep and wait functions globally to speed up test execution.
    Reduces sleep times and WebDriverWait timeouts to minimum.
    """
    # Mock the custom sleep function from seleniumUtil
    with patch('scrapper.seleniumUtil.sleep', return_value=None) as mock_selenium_sleep:
        # Mock time.sleep across all modules
        with patch('time.sleep', return_value=None) as mock_time_sleep:
            # Mock WebDriverWait to avoid timeout delays
            # Create a mock that immediately calls the condition function
            def mock_wait_until(condition, *args, **kwargs):
                try:
                    # Try to execute the condition immediately
                    return condition(None)
                except:
                    # If condition fails, return a mock object
                    from unittest.mock import MagicMock
                    return MagicMock()
            
            with patch('selenium.webdriver.support.ui.WebDriverWait') as MockWebDriverWait:
                # Configure the mock to return an object with an 'until' method
                mock_instance = MockWebDriverWait.return_value
                mock_instance.until.side_effect = mock_wait_until
                
                yield {
                    'selenium_sleep': mock_selenium_sleep,
                    'time_sleep': mock_time_sleep,
                    'webdriver_wait': MockWebDriverWait
                }

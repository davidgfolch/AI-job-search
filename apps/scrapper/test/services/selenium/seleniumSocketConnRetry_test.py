import pytest
import urllib3
from unittest.mock import MagicMock, patch
from scrapper.services.selenium.seleniumSocketConnRetry import seleniumSocketConnRetry

def test_selenium_socket_conn_retry_success():
    mock_func = MagicMock(return_value="success")
    mock_func.__name__ = "mock_func"
    decorated = seleniumSocketConnRetry()(mock_func)
    
    result = decorated()
    
    assert result == "success"
    assert mock_func.call_count == 1

def test_selenium_socket_conn_retry_recovers():
    # It should retry on ReadTimeoutError and eventually succeed
    mock_func = MagicMock()
    mock_func.__name__ = "mock_func"
    mock_func.side_effect = [
        urllib3.exceptions.ReadTimeoutError(None, None, "timeout"),
        urllib3.exceptions.ReadTimeoutError(None, None, "timeout"),
        "success"
    ]
    
    # Use small delay for tests
    with patch('commonlib.decorator.retry.sleep'): # Mock sleep to speed up tests
        decorated = seleniumSocketConnRetry()(mock_func)
        result = decorated()
    
    assert result == "success"
    assert mock_func.call_count == 3

def test_selenium_socket_conn_retry_fails_after_limit():
    # It should raise the exception after max retries (default is 20 in seleniumSocketConnRetry)
    # Let's test with a smaller number if we can, but since it's hardcoded in the decorator factory
    # we just mock many failures.
    
    mock_func = MagicMock()
    mock_func.__name__ = "mock_func"
    mock_func.side_effect = urllib3.exceptions.ReadTimeoutError(None, None, "timeout")
    
    # The decorator is configured for 20 retries + 1 initial call = 21 attempts
    # Actually looking at retry.py: for i in range(1, retries + 2):
    # retries=20 -> range(1, 22) -> 21 attempts.
    
    with patch('commonlib.decorator.retry.sleep'):
        decorated = seleniumSocketConnRetry()(mock_func)
        with pytest.raises(urllib3.exceptions.ReadTimeoutError):
            decorated()
            
    assert mock_func.call_count == 21

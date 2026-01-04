import pytest

from commonlib.decorator.retry import retry
from commonlib.decorator.retry import StackTrace

def test_retry_success():
    
    @retry(retries=3, delay=1)
    def always_succeeds():
        return "success"
    
    assert always_succeeds() == "success"

def test_retry_eventual_success():
    call_count = 0

    @retry(retries=3, delay=1)
    def succeeds_after_two_tries():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Fail")
        return "success"
    
    assert succeeds_after_two_tries() == "success"
    assert call_count == 3

def test_retry_eventual_failure():
    @retry(retries=3, delay=1, raiseException=False)
    def always_fails():
        raise ValueError("Fail")
    
    assert always_fails() is False

def test_retry_custom_exception_handling():
    custom_exception_handled = False

    def custom_exception_handler():
        nonlocal custom_exception_handled
        custom_exception_handled = True

    @retry(retries=3, delay=1, exceptionFnc=custom_exception_handler)
    def always_fails():
        raise ValueError("Fail")
    
    with pytest.raises(ValueError):
        always_fails()
    assert custom_exception_handled

def test_retry_stacktrace_always():
    @retry(retries=1, delay=1, stackStrace=StackTrace.ALWAYS)
    def always_fails():
        raise ValueError("Fail")
    
    with pytest.raises(ValueError):
        always_fails()

def test_retry_stacktrace_never():
    @retry(retries=1, delay=1, stackStrace=StackTrace.NEVER)
    def always_fails():
        raise ValueError("Fail")
    
    with pytest.raises(ValueError):
        always_fails()
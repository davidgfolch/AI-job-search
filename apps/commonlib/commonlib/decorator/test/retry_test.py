import pytest
from unittest.mock import MagicMock, patch
from commonlib.decorator.retry import retry, StackTrace


class TestRetry:
    def test_retry_success_first_try(self):
        @retry(retries=3, delay=0.001)
        def success():
            return "ok"
        assert success() == "ok"

    def test_retry_success_after_failures(self):
        call_count = [0]
        @retry(retries=3, delay=0.001)
        def flaky():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("not yet")
            return "done"
        assert flaky() == "done"
        assert call_count[0] == 3

    def test_retry_exhausted_raises(self):
        @retry(retries=2, delay=0.001)
        def always_fail():
            raise ValueError("boom")
        with pytest.raises(ValueError, match="boom"):
            always_fail()

    def test_retry_exhausted_no_raise(self):
        @retry(retries=2, delay=0.001, raiseException=False)
        def always_fail():
            raise ValueError("boom")
        result = always_fail()
        assert result is False

    def test_retry_keyboard_interrupt_propagates(self):
        @retry(retries=3, delay=0.001)
        def keyboard_interrupt():
            raise KeyboardInterrupt()
        with pytest.raises(KeyboardInterrupt):
            keyboard_interrupt()

    def test_retry_validates_retries(self):
        with pytest.raises(ValueError, match="retries should be"):
            @retry(retries=0, delay=1)
            def f(): pass

    def test_retry_validates_delay(self):
        with pytest.raises(ValueError, match="retries should be"):
            @retry(retries=1, delay=0)
            def f2(): pass

    def test_retry_exception_callback(self):
        callback = MagicMock()
        @retry(retries=2, delay=0.001, exceptionFnc=callback)
        def fail():
            raise ValueError("err")
        with pytest.raises(ValueError):
            fail()
        assert callback.called

    def test_retry_exception_callback_with_args(self):
        callback = MagicMock()
        @retry(retries=2, delay=0.001, exceptionFnc=callback)
        def fail(x):
            raise ValueError("err")
        with pytest.raises(ValueError):
            fail(42)
        callback.assert_called_with(42)

    def test_retry_stack_trace_always(self):
        @retry(retries=1, delay=0.001, stackTrace=StackTrace.ALWAYS)
        def fail():
            raise ValueError("err")
        with pytest.raises(ValueError):
            fail()

    def test_retry_stack_trace_never(self):
        @retry(retries=1, delay=0.001, stackTrace=StackTrace.NEVER, raiseException=False)
        def fail():
            raise ValueError("err")
        result = fail()
        assert result is False

    def test_retry_returns_false_on_exhausted(self):
        @retry(retries=1, delay=0.001, raiseException=False)
        def fail():
            raise ValueError("err")
        assert fail() is False

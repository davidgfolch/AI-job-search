import pytest
from unittest.mock import patch
from aiEnrich3.main import run


def test_run_loop_termination():
    # Setup the mock so that:
    # 1. First call: returns processed=10, pipeline="pipe1" -> goes to `continue`, skipping the idle wait.
    # 2. Second call: returns processed=0, pipeline="pipe1" -> skips continue and logs the idle wait.
    # 3. Third call: raises Exception to break the infinite loop.
    with (
        patch("aiEnrich3.main.get_job_enabled", return_value=True),
        patch("aiEnrich3.main.get_skill_enabled", return_value=False),
        patch("aiEnrich3.main.dataExtractor") as mock_data_extractor,
        patch("aiEnrich3.main.logIdleWait") as mock_idle_wait,
    ):
        mock_data_extractor.side_effect = [
            (10, "pipe1"),
            (0, "pipe1"),
            Exception("Loop Exit"),
        ]

        with pytest.raises(Exception, match="Loop Exit"):
            run()

        assert mock_data_extractor.call_count == 3
        mock_idle_wait.assert_called_once()
        assert mock_idle_wait.call_args.args[1:] == ("10s", "jobs.skipped")
        assert mock_idle_wait.call_args.kwargs == {"reason": "no_pending_jobs"}
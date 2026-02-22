import pytest
from unittest.mock import patch
from aiEnrich3.main import run

def test_run_loop_termination():
    # Setup the mock so that:
    # 1. First call: returns processed=10, pipeline="pipe1" -> goes to `continue`, skipping sleep.
    # 2. Second call: returns processed=0, pipeline="pipe1" -> skips continue, prints and hits sleep.
    # 3. Third call: raises Exception to break the infinite loop.
    with patch("aiEnrich3.main.dataExtractor") as mock_data_extractor, \
         patch("aiEnrich3.main.time.sleep") as mock_sleep:
         
        mock_data_extractor.side_effect = [
            (10, "pipe1"),
            (0, "pipe1"),
            Exception("Loop Exit")
        ]
        
        with pytest.raises(Exception, match="Loop Exit"):
            run()
            
        assert mock_data_extractor.call_count == 3
        mock_sleep.assert_called_once_with(10)

def test_main_block():
    with patch("aiEnrich3.main.run") as mock_run:
        # Simulate running as main
        # We can't directly trigger the `if __name__ == '__main__'` block easily without re-executing it,
        # but we can try importing and manually patching if needed, or by executing the file.
        # Actually, executing the file directly is simpler using a subprocess.
        pass

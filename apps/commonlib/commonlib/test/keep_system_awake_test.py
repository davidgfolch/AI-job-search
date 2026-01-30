import unittest
import time
from commonlib.keep_system_awake import KeepSystemAwake

class TestKeepSystemAwake(unittest.TestCase):
    def test_keep_system_awake(self):
        print("\nTesting KeepSystemAwake...")
        try:
            with KeepSystemAwake() as k:
                print("Inside context manager")
                time.sleep(0.01)
            print("KeepSystemAwake test passed (no exceptions)")
        except Exception as e:
            self.fail(f"KeepSystemAwake failed with exception: {e}")

if __name__ == '__main__':
    unittest.main()

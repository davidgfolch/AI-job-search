import unittest
import time
from commonlib.keep_system_awake import KeepSystemAwake
from commonlib.wake_timer import WakeableTimer

class TestPowerManagement(unittest.TestCase):
    def test_keep_system_awake(self):
        print("\nTesting KeepSystemAwake...")
        try:
            with KeepSystemAwake() as k:
                print("Inside context manager")
                time.sleep(1)
            print("KeepSystemAwake test passed (no exceptions)")
        except Exception as e:
            self.fail(f"KeepSystemAwake failed with exception: {e}")

    def test_wake_timer(self):
        print("\nTesting WakeableTimer...")
        timer = WakeableTimer()
        seconds = 2
        print(f"Waiting for {seconds} seconds...")
        start_time = time.time()
        timer.wait(seconds)
        elapsed = time.time() - start_time
        print(f"Waited for {elapsed:.2f} seconds")
        self.assertGreaterEqual(elapsed, seconds, "Timer returned too early")
        self.assertLess(elapsed, seconds + 1, "Timer took too long")

if __name__ == '__main__':
    unittest.main()

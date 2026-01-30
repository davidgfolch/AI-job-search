import unittest
import time
from commonlib.wake_timer import WakeableTimer

class TestWakeableTimer(unittest.TestCase):
    def test_wake_timer(self):
        print("\nTesting WakeableTimer...")
        timer = WakeableTimer()
        seconds = 0.5
        print(f"Waiting for {seconds} seconds...")
        start_time = time.time()
        timer.wait(seconds)
        elapsed = time.time() - start_time
        print(f"Waited for {elapsed:.2f} seconds")
        self.assertGreaterEqual(elapsed, seconds, "Timer returned too early")
        self.assertLess(elapsed, seconds + 1, "Timer took too long")

if __name__ == '__main__':
    unittest.main()

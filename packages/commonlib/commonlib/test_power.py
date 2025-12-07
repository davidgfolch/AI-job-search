import unittest
import sys
import os
import time
import importlib.util

# Helper to import module from path
def import_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Define paths
base_dir = os.path.dirname(__file__)
keep_system_awake_path = os.path.join(base_dir, 'keep_system_awake.py')
wake_timer_path = os.path.join(base_dir, 'wake_timer.py')

# Import modules directly
keep_system_awake_mod = import_from_path('keep_system_awake_mod', keep_system_awake_path)
wake_timer_mod = import_from_path('wake_timer_mod', wake_timer_path)

KeepSystemAwake = keep_system_awake_mod.KeepSystemAwake
WakeableTimer = wake_timer_mod.WakeableTimer

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

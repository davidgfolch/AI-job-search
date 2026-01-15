import sys
import os

# Adjust path to find commonlib
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../commonlib')))

from commonlib.decorator.retry import retry

class TestClass:
    def close_modal(self):
        print("close_modal called")

    @retry(retries=1, exception=Exception, exceptionFnc=lambda self, *a, **k: self.close_modal())
    def load_job_detail(self, arg):
        print(f"load_job_detail called with {arg}")
        raise Exception("Oops")

    def scroll_to_bottom(self):
        print("scroll_to_bottom called")

    # This mimics the potentially broken code in indeedNavigator.py:75
    # @retry(exceptionFnc=lambda self: self.scroll_to_bottom())
    # def scroll_jobs_list(self, idx):
    
    # I will replicate the exact lambda signature used in indeedNavigator.py line 75
    @retry(retries=1, exception=Exception, exceptionFnc=lambda self: self.scroll_to_bottom())
    def scroll_jobs_list(self, idx):
        print(f"scroll_jobs_list called with {idx}")
        raise Exception("Oops")

def run_tests():
    t = TestClass()
    print("--- Testing load_job_detail fix ---")
    try:
        t.load_job_detail("myArg")
    except Exception as e:
        print(f"load_job_detail finished with exception: {e}")

    print("\n--- Testing scroll_jobs_list original ---")
    try:
        t.scroll_jobs_list(1)
    except TypeError as e:
        print(f"DETECTED BROKEN BEHAVIOR: TypeError caught: {e}")
    except Exception as e:
        print(f"scroll_jobs_list finished with exception: {e}")

if __name__ == "__main__":
    run_tests()


import threading
import time
import sys
import os

# Add packages to path
sys.path.append(os.path.join(os.getcwd(), 'packages', 'commonlib'))
sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))

from commonlib.mysqlUtil import MysqlUtil, getConnection

def worker(worker_id):
    try:
        # Simulate a request
        db = MysqlUtil(getConnection())
        with db:
            # Just check if we can get a connection and run a query
            # We use a simple query that doesn't depend on specific tables if possible,
            # or just SELECT 1
            with db.cursor() as c:
                c.execute("SELECT 1")
                result = c.fetchone()
                # print(f"Worker {worker_id}: Got {result}")
                time.sleep(0.1) # Simulate some work
    except Exception as e:
        print(f"Worker {worker_id} failed: {e}")
        return False
    return True

def run_test():
    threads = []
    num_workers = 10
    
    print(f"Starting {num_workers} concurrent workers...")
    
    for i in range(num_workers):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    print("All workers finished.")

if __name__ == "__main__":
    run_test()

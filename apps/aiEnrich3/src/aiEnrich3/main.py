import sys
import io

# Fix encoding issue for printing special characters in Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from aiEnrich3.dataExtractor import dataExtractor
from aiEnrich3.pipeline import ExtractionPipeline
from commonlib.terminalColor import cyan
from typing import Optional
import time

def run():
    pipeline: Optional[ExtractionPipeline] = None
    while True:
        processed, pipeline = dataExtractor(pipeline)
        if processed > 0:
            continue
            
        print(cyan('All jobs enriched. I\'ll retry in 10s ...'), flush=True)
        time.sleep(10)

if __name__ == "__main__":
    run()

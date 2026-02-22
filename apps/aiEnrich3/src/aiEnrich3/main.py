import sys
import io
import time
from typing import Optional

from aiEnrich3.dataExtractor import dataExtractor
from aiEnrich3.pipeline import ExtractionPipeline
from commonlib.terminalColor import cyan

def run():
    pipeline: Optional[ExtractionPipeline] = None
    while True:
        processed, pipeline = dataExtractor(pipeline)
        if processed > 0:
            continue
            
        print(cyan('All jobs enriched. I\'ll retry in 10s ...'), flush=True)
        time.sleep(10)

if __name__ == "__main__":
    # Fix encoding issue for printing special characters in Windows terminal
    if sys.stdout and hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    run()

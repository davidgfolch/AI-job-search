import statistics
import time

from .terminalColor import yellow
from commonlib.observability import get_logger

logger = get_logger("commonlib.stopWatch")


class StopWatch:
    def __init__(self):
        self.times = []
        self.startTime = None

    def start(self):
        self.startTime = time.time()

    def elapsed(self):
        end = time.time()
        elapsed = end-self.startTime
        print(yellow(f'Time elapsed: {elapsed} secs.'), end='\r')

    def end(self):
        end = time.time()
        timeElapsed = end-self.startTime
        self.times.append(timeElapsed)
        logger.info("timer.elapsed", elapsed_secs=round(timeElapsed, 2), median_secs=round(statistics.median(self.times), 2), samples=len(self.times))

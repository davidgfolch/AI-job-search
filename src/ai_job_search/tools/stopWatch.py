import statistics
import time

from ai_job_search.tools.terminalColor import yellow


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
        print(f'Time elapsed: {timeElapsed} secs.')
        print(yellow(f'Media time elapsed: {statistics.median(self.times)}'))

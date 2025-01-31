

import statistics
import time

from ai_job_search.tools.terminalColor import yellow

times = []
startTime = time.time()


def start():
    global startTime
    startTime = time.time()


def elapsed():
    end = time.time()
    elapsed = end-startTime
    print(yellow(f'Time elapsed: {elapsed} secs.', end='\r'))


def end():
    global times
    end = time.time()
    timeElapsed = end-startTime
    times.append(timeElapsed)
    print(f'Time elapsed: {timeElapsed} secs.')
    print(yellow(f'Media time elapsed: {statistics.median(times)}'))

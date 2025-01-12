

import statistics
import time

from ai_job_search.tools.terminalColor import yellow

times = []
startTime = time.time()


def start():
    global startTime
    startTime = time.time()


def end():
    global times
    end = time.time()
    timeElapsed = end-startTime
    times.append(timeElapsed)
    print(f'Time elapsed: {timeElapsed} secs.')
    print(yellow(f'Total processed jobs: {len(times)}'))
    print(yellow(f'Media time elapsed: {statistics.median(times)}'))
    print()
    print()

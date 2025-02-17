import re
import time
from ai_job_search.tools.stopWatch import StopWatch

def test_start():
    time1 = time.time()
    sut = StopWatch()
    sut.start()
    time2 = time.time()
    assert time1 <= sut.startTime
    assert sut.startTime <= time2

def test_elapsed(capsys):
    sut = StopWatch()
    sut.start()
    time.sleep(0.5)
    sut.elapsed()
    captured = capsys.readouterr()
    assert isinstance(re.search('Time elapsed: 0.5[0-9]+ secs[.]',captured.out), re.Match)

def test_end(capsys):
    sut = StopWatch()
    sut.start()
    time.sleep(0.5)
    sut.end()
    captured = capsys.readouterr()
    assert isinstance(re.search('Time elapsed: 0.5[0-9]+ secs[.]',captured.out), re.Match)
    assert isinstance(re.search('Media time elapsed: 0.5[0-9]+',captured.out), re.Match)

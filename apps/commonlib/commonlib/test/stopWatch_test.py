import re
import time

from structlog.testing import capture_logs

from commonlib.stopWatch import StopWatch


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

def test_end():
    sut = StopWatch()
    sut.start()
    time.sleep(0.5)
    with capture_logs() as records:
        sut.end()
    elapsed = [r for r in records if r["event"] == "timer.elapsed"]
    assert len(elapsed) == 1
    assert elapsed[0]["elapsed_secs"] >= 0.5
    assert elapsed[0]["samples"] == 1
    assert "median_secs" in elapsed[0]
    assert elapsed[0]["module"] == "commonlib.stopWatch"


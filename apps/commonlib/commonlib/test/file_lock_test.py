import os

import pytest

from commonlib.file_lock import try_lock, unlock


@pytest.fixture
def lock_fds(tmp_path):
    """Two handles on the same lock file, standing in for two processes."""
    path = tmp_path / "slot.lock"
    fds = [os.open(path, os.O_RDWR | os.O_CREAT, 0o644) for _ in range(2)]
    yield fds
    for fd in fds:
        try:
            os.close(fd)
        except OSError:
            pass


def _flocked_shared_and_exclusive(lock_fds):
    """POSIX shared locks do not exclude each other, Windows has exclusive locks only."""
    return os.name == "posix"


class TestTryLock:

    def test_exclusive_lock_excludes_a_second_holder(self, lock_fds):
        assert try_lock(lock_fds[0], shared=False) is True
        assert try_lock(lock_fds[1], shared=False) is False

    def test_second_holder_succeeds_after_the_first_unlocks(self, lock_fds):
        assert try_lock(lock_fds[0], shared=False) is True
        unlock(lock_fds[0])
        assert try_lock(lock_fds[1], shared=False) is True

    def test_shared_lock_excludes_an_exclusive_one(self, lock_fds):
        assert try_lock(lock_fds[0], shared=True) is True
        assert try_lock(lock_fds[1], shared=False) is False

    def test_shared_locks_do_not_exclude_each_other(self, lock_fds):
        assert try_lock(lock_fds[0], shared=True) is True
        assert try_lock(lock_fds[1], shared=True) is _flocked_shared_and_exclusive(lock_fds)


class TestUnlock:

    def test_unlocking_a_free_descriptor_is_harmless(self, lock_fds):
        unlock(lock_fds[0])
        assert try_lock(lock_fds[0], shared=False) is True

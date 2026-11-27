import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import crx3


class TestExtensionId:
    def test_derives_id_from_public_key(self):
        public_key = b"example-public-key"
        digest = hashlib.sha256(public_key).hexdigest()[:32]
        expected = "".join(chr(ord("a") + int(char, 16)) for char in digest)
        assert crx3.extension_id(public_key) == expected
        assert len(crx3.extension_id(public_key)) == 32

    def test_rejects_non_crx_data(self, tmp_path):
        path = tmp_path / "bad.crx"
        path.write_bytes(b"not a crx")
        try:
            crx3.crx3_public_key(path)
        except ValueError:
            return
        raise AssertionError("Expected ValueError for invalid CRX data")

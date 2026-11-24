import pytest
from unittest.mock import Mock
from scrapper.services.gmail.email_deleter import delete_email


class TestDeleteEmail:
    @pytest.mark.parametrize("email_id, store_side_effect, expected", [
        (b"123", None, True),
        (b"123", Exception("Fail"), False),
        ("123", None, True),
    ])
    def test_delete_email(self, email_id, store_side_effect, expected):
        imap = Mock()
        if store_side_effect:
            imap.store.side_effect = store_side_effect
        assert delete_email(imap, email_id) is expected
        imap.store.assert_called_once_with("123", "+FLAGS", "\\Deleted")
        assert imap.expunge.called is expected

import pytest
from unittest.mock import Mock, patch, MagicMock
from scrapper.services.gmail.email_reader import EmailReader
from scrapper.services.gmail.email_exceptions import GmailConnectionError, VerificationCodeExtractionError
from email.message import EmailMessage

class TestEmailReader:
    @pytest.fixture
    def email_reader(self):
        return EmailReader("test@example.com", "password")

    @pytest.fixture
    def mock_imap(self):
        with patch("imaplib.IMAP4_SSL") as mock:
            yield mock

    def test_connect(self, mock_imap, email_reader):
        assert email_reader.connect() is True
        mock_imap.assert_called_with("imap.gmail.com", 993)
        mock_imap.return_value.login.assert_called_with("test@example.com", "password")

    def test_connect_failure(self, mock_imap, email_reader):
        mock_imap.side_effect = Exception("Connection failed")
        with pytest.raises(GmailConnectionError):
            email_reader.connect()

    @pytest.mark.parametrize("side_effect, expected", [(None, True), (Exception("Fail"), False)])
    def test_select_inbox(self, email_reader, side_effect, expected):
        email_reader.imap = Mock()
        if side_effect:
            email_reader.imap.select.side_effect = side_effect
        assert email_reader.select_inbox() is expected

    @pytest.mark.parametrize("api_return, expected", [
        (( "OK", [b"1 2 3"]), [b"3", b"2", b"1"]),
        (( "OK", [None]), []), 
        (Exception("Fail"), [])
    ])
    def test_search_emails(self, email_reader, api_return, expected):
        email_reader.imap = Mock()
        if isinstance(api_return, Exception):
            email_reader.imap.search.side_effect = api_return
        else:
            email_reader.imap.search.return_value = api_return
        assert email_reader.search_emails_from_sender_since("s", "d") == expected

    @pytest.mark.parametrize("subject, expected_code", [
        ("Your verification code is 123456", "123456"),
        ("No code here", None),
    ])
    def test_extract_verification_code(self, email_reader, subject, expected_code):
        if expected_code:
            assert email_reader.extract_verification_code_from_subject(subject) == expected_code
        else:
            with pytest.raises(VerificationCodeExtractionError):
                email_reader.extract_verification_code_from_subject(subject)

    def test_close(self, email_reader):
        email_reader.imap = Mock()
        mock_imap = email_reader.imap
        email_reader.close()
        mock_imap.close.assert_called_once()
        assert email_reader.imap is None

    @pytest.mark.parametrize("fetch_side_effect, msg_subject, expected", [
        (None, "Test Subject", "Test Subject"),
        (Exception("Fail"), None, "")
    ])
    def test_get_email_subject(self, email_reader, fetch_side_effect, msg_subject, expected):
        email_reader.imap = Mock()
        if fetch_side_effect:
            email_reader.imap.fetch.side_effect = fetch_side_effect
        else:
            msg = EmailMessage()
            msg["Subject"] = msg_subject
            email_reader.imap.fetch.return_value = ("OK", [(b"1", msg.as_bytes())])
        assert email_reader.get_email_subject(b"1") == expected

    @pytest.mark.parametrize("case_type, content, expected", [
        ("plain", "Hello", "Hello"),
        ("html_only", "<h1>Hi</h1>", "")
    ])
    def test_get_email_body_simple(self, email_reader, case_type, content, expected):
        email_reader.imap = Mock()
        msg = EmailMessage()
        msg["Subject"] = "Test Subject"
        if case_type == "plain":
            msg.set_content(content)
        else:
            msg.add_alternative(content, subtype='html')
            
        email_reader.imap.fetch.return_value = ("OK", [(b"1", msg.as_bytes())])
        
        result = email_reader.get_email_body(b"1")
        if expected:
            assert expected in result
        else:
            assert result == ""

    def test_get_email_body_decoding_failure(self, email_reader):
        email_reader.imap = Mock()
        mock_part = Mock()
        mock_part.get_content_type.return_value = "text/plain"
        mock_part.get_payload.side_effect = [Exception("Decode error"), "fallback"]
        msg = MagicMock()
        msg.walk.return_value = [mock_part]
        email_reader.imap.fetch.return_value = ("OK", [(b"1", b"raw")])
        
        with patch("email.message_from_bytes", return_value=msg), \
             patch("scrapper.services.gmail.email_reader.decode_header", return_value=[("S", "utf-8")]):
            assert email_reader.get_email_body(b"1") == "fallback"

    @patch("scrapper.services.gmail.email_reader.time")
    def test_get_latest_verification_code_flow(self, mock_time, email_reader):
        email_reader.imap = Mock()
        email_reader.connect = Mock()
        email_reader.select_inbox = Mock(return_value=True)
        # 1. Success case
        email_reader.imap.search.side_effect = [("OK", [None]), ("OK", [b"123"])]
        msg = EmailMessage()
        msg["Subject"] = "Code 999999"
        email_reader.imap.fetch.return_value = ("OK", [(b"1", msg.as_bytes())]) 
        mock_time.time.side_effect = range(100, 120)
        assert email_reader.get_latest_verification_code("s", 10) == "999999"

    @patch("scrapper.services.gmail.email_reader.time")
    def test_get_latest_verification_code_timeout(self, mock_time, email_reader):
        email_reader.imap = Mock()
        email_reader.connect = Mock()
        email_reader.select_inbox = Mock(return_value=True)
        email_reader.imap.search.return_value = ("OK", [None])
        mock_time.time.side_effect = [100, 101, 111] # Timeout > 10
        with pytest.raises(GmailConnectionError, match="Timeout"):
            email_reader.get_latest_verification_code("s", 10)

    @patch("scrapper.services.gmail.email_reader.time")
    def test_get_latest_verification_code_bad_extract(self, mock_time, email_reader):
        email_reader.imap = Mock()
        email_reader.connect = Mock()
        email_reader.select_inbox = Mock(return_value=True)
        email_reader.imap.search.return_value = ("OK", [b"123"])
        msg = EmailMessage()
        msg["Subject"] = "No code"
        email_reader.imap.fetch.return_value = ("OK", [(b"1", msg.as_bytes())])
        mock_time.time.side_effect = [100, 101, 105, 111]
        with pytest.raises(GmailConnectionError, match="Timeout"):
            email_reader.get_latest_verification_code("s", 10)

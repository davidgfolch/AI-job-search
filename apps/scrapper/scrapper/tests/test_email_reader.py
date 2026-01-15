import pytest
from unittest.mock import Mock, patch, MagicMock
from scrapper.services.gmail.email_reader import EmailReader
from scrapper.services.gmail.email_exceptions import GmailConnectionError, VerificationCodeExtractionError
import email
from email.message import EmailMessage

class TestEmailReader:
    @pytest.fixture
    def email_reader(self):
        return EmailReader("test@example.com", "password")

    @patch("imaplib.IMAP4_SSL")
    def test_connect_success(self, mock_imap, email_reader):
        mock_instance = mock_imap.return_value
        result = email_reader.connect()
        
        assert result is True
        mock_imap.assert_called_with("imap.gmail.com", 993)
        mock_instance.login.assert_called_with("test@example.com", "password")

    @patch("imaplib.IMAP4_SSL")
    def test_connect_failure(self, mock_imap, email_reader):
        mock_imap.side_effect = Exception("Connection failed")
        
        with pytest.raises(GmailConnectionError):
            email_reader.connect()

    def test_select_inbox_success(self, email_reader):
        email_reader.imap = Mock()
        result = email_reader.select_inbox()
        
        assert result is True
        email_reader.imap.select.assert_called_with("inbox")

    def test_select_inbox_failure(self, email_reader):
        email_reader.imap = Mock()
        email_reader.imap.select.side_effect = Exception("Select failed")
        
        result = email_reader.select_inbox()
        assert result is False

    def test_search_emails_from_sender_since_success(self, email_reader):
        email_reader.imap = Mock()
        email_reader.imap.search.return_value = ("OK", [b"1 2 3"])
        
        results = email_reader.search_emails_from_sender_since("sender@example.com", "01-Jan-2023")
        
        assert results == [b"3", b"2", b"1"]

    def test_search_emails_from_sender_since_empty(self, email_reader):
        email_reader.imap = Mock()
        email_reader.imap.search.return_value = ("OK", [None])
        
        results = email_reader.search_emails_from_sender_since("sender@example.com", "01-Jan-2023")
        
        assert results == []

    def test_search_emails_failure(self, email_reader):
        email_reader.imap = Mock()
        email_reader.imap.search.side_effect = Exception("Search failed")
        
        results = email_reader.search_emails_from_sender_since("sender@example.com", "01-Jan-2023")
        
        assert results == []

    def test_extract_verification_code_success(self, email_reader):
        subject = "Your verification code is 123456"
        code = email_reader.extract_verification_code_from_subject(subject)
        assert code == "123456"

    def test_extract_verification_code_failure(self, email_reader):
        subject = "No code here"
        with pytest.raises(VerificationCodeExtractionError):
            email_reader.extract_verification_code_from_subject(subject)

    def test_close(self, email_reader):
        mock_imap = Mock()
        email_reader.imap = mock_imap
        email_reader.close()
        
        mock_imap.close.assert_called_once()
        mock_imap.logout.assert_called_once()
        assert email_reader.imap is None

    def test_get_email_subject_success(self, email_reader):
        email_reader.imap = Mock()
        
        msg = EmailMessage()
        msg["Subject"] = "Test Subject"
        msg_bytes = msg.as_bytes()
        
        email_reader.imap.fetch.return_value = ("OK", [(b"1", msg_bytes)])
        
        subject = email_reader.get_email_subject(b"1")
        assert subject == "Test Subject"

    def test_get_email_subject_failure(self, email_reader):
        email_reader.imap = Mock()
        email_reader.imap.fetch.side_effect = Exception("Fetch failed")
        
        subject = email_reader.get_email_subject(b"1")
        assert subject == ""

    def test_get_email_body_text_plain(self, email_reader):
        email_reader.imap = Mock()
        
        # Create a multipart message with text/plain
        msg = EmailMessage()
        msg.set_content("Hello World")
        msg["Subject"] = "Test"
        msg_bytes = msg.as_bytes()
        
        email_reader.imap.fetch.return_value = ("OK", [(b"1", msg_bytes)])
        
        body = email_reader.get_email_body(b"1")
        assert "Hello World" in body

    def test_get_email_body_no_text_plain(self, email_reader):
        email_reader.imap = Mock()
        
        # Create a message with only html
        msg = EmailMessage()
        msg.add_alternative("<h1>Hello World</h1>", subtype='html')
        msg["Subject"] = "Test"
        msg_bytes = msg.as_bytes()
        
        email_reader.imap.fetch.return_value = ("OK", [(b"1", msg_bytes)])
        
        # Method returns empty string if no text/plain found in multipart? 
        # Actually logic is: if multipart, it looks for text/plain. If not found, it breaks loop?
        # Let's check source code logic. 
        # for part in msg.walk(): if part.get_content_type() == "text/plain": body = ... break
        # So if no text/plain, body remains ""
        
        body = email_reader.get_email_body(b"1")
        assert body == ""

    def test_get_email_body_decoding_failure(self, email_reader):
        email_reader.imap = Mock()
        
        # Create a mock part that raises error on decode
        mock_part = Mock()
        mock_part.get_content_type.return_value = "text/plain"
        
        # If get_payload raises:
        mock_part.get_payload.side_effect = [Exception("Decode error"), "fallback_content"]
        
        # msg.walk() returns list of parts.
        msg = MagicMock()
        msg.is_multipart.return_value = True
        msg.walk.return_value = [mock_part]
        
        email_reader.imap.fetch.return_value = ("OK", [(b"1", b"raw_data")])
        
        # We also need email.message_from_bytes to return our msg mock
        with patch("email.message_from_bytes", return_value=msg):
            with patch("scrapper.services.gmail.email_reader.decode_header", return_value=[("Subject", "utf-8")]):
                 body = email_reader.get_email_body(b"1")
        
        assert body == "fallback_content"

    @patch("scrapper.services.gmail.email_reader.time")
    def test_get_latest_verification_code_success(self, mock_time, email_reader):
        email_reader.imap = Mock()
        email_reader.connect = Mock()
        email_reader.select_inbox = Mock(return_value=True)
        
        # Setup search response: first empty, then one email
        # search returns (status, [ids])
        # First call: empty
        # Second call: one id
        email_reader.imap.search.side_effect = [
            ("OK", [None]), 
            ("OK", [b"123"])
        ]
        
        # Setup fetch for subject extraction
        msg = EmailMessage()
        msg["Subject"] = "Your code is 999999"
        msg_bytes = msg.as_bytes()
        email_reader.imap.fetch.return_value = ("OK", [(b"1", msg_bytes)])
        
        # Mock time.time to simulate timeout loop (start, start+1, start+timeout+1) 
        # But here we want success.
        mock_time.time.side_effect = [100, 101, 102, 103, 104, 105] 
        
        code = email_reader.get_latest_verification_code("sender", timeout=10)
        assert code == "999999"

    @patch("scrapper.services.gmail.email_reader.time")
    def test_get_latest_verification_code_timeout(self, mock_time, email_reader):
        email_reader.imap = Mock()
        email_reader.connect = Mock()
        email_reader.select_inbox = Mock(return_value=True)
        
        email_reader.imap.search.return_value = ("OK", [None])
        
        # time.time() increases until timeout
        # loop condition: time.time() - start_time < timeout
        # start=100. timeout=10.
        # side_effect: 100 (start), 101, 105, 111 (loop break)
        mock_time.time.side_effect = [100, 101, 105, 111]
        
        with pytest.raises(GmailConnectionError, match="Timeout"):
            email_reader.get_latest_verification_code("sender", timeout=10)

    @patch("scrapper.services.gmail.email_reader.time")
    def test_get_latest_verification_code_extraction_error(self, mock_time, email_reader):
        email_reader.imap = Mock()
        email_reader.connect = Mock()
        email_reader.select_inbox = Mock(return_value=True)
        
        email_reader.imap.search.return_value = ("OK", [b"123"])
        
        msg = EmailMessage()
        msg["Subject"] = "No code here"
        msg_bytes = msg.as_bytes()
        email_reader.imap.fetch.return_value = ("OK", [(b"1", msg_bytes)])
        
        # It will loop. Force timeout for test or make it return success on second try?
        # The logic: if extract fails, it prints and continues loop.
        # So it will retry. existing logic: check last_checked_id.
        # IF ID is same, it doesn't try again right away?
        # logic: 
        # if email_ids:
        #    latest = ids[-1]
        #    if latest != last_checked: -> try extract.
        #       if fail: last_checked = latest.
        # So next loop, if same ID, it skips extraction block.
        # Eventually timeout.
        
        mock_time.time.side_effect = [100, 101, 105, 111]
        
        with pytest.raises(GmailConnectionError, match="Timeout"):
            email_reader.get_latest_verification_code("sender", timeout=10)

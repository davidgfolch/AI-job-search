import re
import time
import email
import imaplib
from email.header import decode_header
from typing import List, Tuple, Optional
from commonlib.terminalColor import yellow
from .email_exceptions import GmailConnectionError, VerificationCodeExtractionError


class EmailReader:
    def __init__(self, email_address: str, app_password: str):
        self.email_address = email_address
        self.app_password = app_password
        self.imap_server = None
        self.imap = None

    def connect(self) -> bool:
        """Connect to Gmail IMAP server"""
        try:
            self.imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            self.imap.login(self.email_address, self.app_password)
            print(f"Successfully connected to Gmail for {self.email_address}")
            return True
        except Exception as e:
            print(yellow(f"Failed to connect to Gmail: {e}"))
            raise GmailConnectionError(f"Failed to connect to Gmail: {e}")

    def select_inbox(self) -> bool:
        """Select the inbox folder"""
        try:
            self.imap.select("inbox")
            return True
        except Exception as e:
            print(yellow(f"Failed to select inbox: {e}"))
            return False

    def search_emails_from_sender_since(self, sender: str, since_date: str, limit: int = 10) -> List[bytes]:
        """Search for emails from a specific sender since a given date"""
        try:
            search_criteria = f'(FROM "{sender}" SINCE {since_date})'
            _, messages = self.imap.search(None, search_criteria)
            email_ids = messages[0].split() if messages[0] else []
            return list(reversed(email_ids[-limit:])) if email_ids else []
        except Exception as e:
            print(yellow(f"Failed to search emails: {e}"))
            return []

    def get_email_body(self, email_id: bytes) -> str:
        """Extract email body from email"""
        try:
            _, msg_data = self.imap.fetch(email_id.decode(), "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    # Decode email subject
                    subject = decode_header(msg["Subject"])[0][0]
                    print("subject:", subject)
                    if isinstance(subject, bytes):
                        subject = subject.decode()
                    # Extract email body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                try:
                                    body = part.get_payload(decode=True).decode()
                                except:
                                    try:
                                        body = part.get_payload(decode=False)
                                    except:
                                        body = str(part)
                                break
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode()
                        except:
                            body = msg.get_payload(decode=False)
                    return body
            return ""
        except Exception as e:
            print(yellow(f"Failed to extract email body for ID {email_id}: {e}"))
            return ""

    def extract_verification_code_from_subject(self, subject: str) -> str:
        """Extract 6-digit verification code from email subject"""
        try:
            # Standard 6+ digit code
            match = re.search(r"\b(\d{6,})\b", subject, re.IGNORECASE | re.MULTILINE)
            if match and match.groups():
                return match.group(1)
            raise VerificationCodeExtractionError("No verification code found in email subject")
        except Exception as e:
            print(yellow(f"Failed to extract verification code from subject: {e}"))
            raise VerificationCodeExtractionError(f"Failed to extract verification code from subject: {e}")

    def get_email_subject(self, email_id: bytes) -> str:
        """Extract email subject from email"""
        try:
            _, msg_data = self.imap.fetch(email_id.decode(), "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    # Decode email subject
                    subject = decode_header(msg["Subject"])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()
                    return subject
            return ""
        except Exception as e:
            print(yellow(f"Failed to extract email subject for ID {email_id}: {e}"))
            return ""

    def get_latest_verification_code(self, sender: str, timeout: int = 120) -> str:
        """Wait for and extract the latest verification code from a sender"""
        from datetime import datetime, timedelta

        start_time = time.time()
        start_datetime = datetime.now()
        last_checked_id = None
        while time.time() - start_time < timeout:
            try:
                if not self.imap:
                    self.connect()
                if not self.select_inbox():
                    raise GmailConnectionError("Could not select inbox")
                # Search emails from sender after start time
                date_str = start_datetime.strftime("%d-%b-%Y")
                search_criteria = f'(FROM "{sender}" SINCE {date_str})'
                _, messages = self.imap.search(None, search_criteria)
                email_ids = messages[0].split() if messages[0] else []
                if email_ids:
                    latest_email_id = email_ids[-1]  # Most recent email
                    if last_checked_id != latest_email_id:
                        email_subject = self.get_email_subject(latest_email_id)
                        if email_subject:
                            try:
                                code = self.extract_verification_code_from_subject(email_subject)
                                print(f"Successfully extracted verification code: {code}")
                                return code
                            except VerificationCodeExtractionError:
                                print("Email found but no verification code in subject...")
                                last_checked_id = latest_email_id
                time.sleep(5)
            except GmailConnectionError:
                try:
                    self.close()
                    self.connect()
                except:
                    time.sleep(10)
            except Exception as e:
                print(yellow(f"Error while waiting for verification code: {e}"))
                time.sleep(5)
        raise GmailConnectionError(f"Timeout: No verification code received within {timeout} seconds")

    def close(self):
        """Close the IMAP connection"""
        try:
            if self.imap:
                self.imap.close()
                self.imap.logout()
                self.imap = None
        except:
            pass

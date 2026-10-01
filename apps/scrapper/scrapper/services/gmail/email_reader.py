import re
import time
import email
import imaplib
from email.header import decode_header
from typing import List, Tuple, Optional
from commonlib.observability import get_logger
from commonlib.terminalColor import yellow
from .email_exceptions import GmailConnectionError, VerificationCodeExtractionError

logger = get_logger("scrapper.email_reader")


def _message_ref(email_id) -> str:
    return email_id.decode() if isinstance(email_id, bytes) else str(email_id)


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
            logger.info("gmail.imap_connected", host="imap.gmail.com", port=993,
                        console=f"Successfully connected to Gmail for {self.email_address}")
            return True
        except Exception as e:
            logger.error("gmail.imap_connect_failed", error=str(e), console=yellow(f"Failed to connect to Gmail: {e}"))
            raise GmailConnectionError(f"Failed to connect to Gmail: {e}")

    def select_inbox(self) -> bool:
        """Select the inbox folder"""
        try:
            self.imap.select("inbox")
            return True
        except Exception as e:
            logger.error("gmail.inbox_select_failed", error=str(e), console=yellow(f"Failed to select inbox: {e}"))
            return False

    def search_emails_from_sender_since(self, sender: str, since_date: str, limit: int = 10) -> List[bytes]:
        """Search for emails from a specific sender since a given date"""
        try:
            search_criteria = f'(FROM "{sender}" SINCE {since_date})'
            _, messages = self.imap.search(None, search_criteria)
            email_ids = messages[0].split() if messages[0] else []
            return list(reversed(email_ids[-limit:])) if email_ids else []
        except Exception as e:
            logger.error("gmail.search_failed", error=str(e), console=yellow(f"Failed to search emails: {e}"))
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
                    logger.info("gmail.subject_decoded", subject_length=len(str(subject)), console="subject decoded")
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
            logger.error("gmail.body_extract_failed", message_id=_message_ref(email_id), error=str(e),
                           console=yellow(f"Failed to extract email body for ID {email_id}: {e}"))
            return ""

    def extract_verification_code_from_subject(self, subject: str) -> str:
        """Extract verification code from email subject (4-6 digits)"""
        try:
            logger.info("gmail.code_extraction_started", subject_length=len(subject), console="subject decoded, extracting verification code")
            match = re.search(r"(\d{4,6})", subject)
            if match and match.groups():
                return match.group(1)
            raise VerificationCodeExtractionError("No verification code found in email subject")
        except Exception as e:
            logger.warning("gmail.code_extraction_failed", subject_length=len(subject), error=str(e),
                            console=yellow(f"Failed to extract verification code from subject: {e}"))
            raise VerificationCodeExtractionError(f"Failed to extract verification code from subject: {e}")

    def get_email_subject(self, email_id: bytes) -> str:
        """Extract email subject from email"""
        try:
            _, msg_data = self.imap.fetch(email_id.decode(), "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    raw_subject = msg["Subject"]
                    if not raw_subject:
                        return ""
                    parts = decode_header(raw_subject)
                    decoded_parts = []
                    for content, charset in parts:
                        if isinstance(content, bytes):
                            decoded_parts.append(content.decode(charset or "utf-8", errors="replace"))
                        else:
                            decoded_parts.append(content)
                    return "".join(decoded_parts)
            return ""
        except Exception as e:
            logger.error("gmail.subject_extract_failed", message_id=_message_ref(email_id), error=str(e),
                           console=yellow(f"Failed to extract email subject for ID {email_id}: {e}"))
            return ""

    def get_latest_verification_code(self, sender: str, timeout: int = 120) -> str:
        """Wait for and extract the latest verification code from a sender"""
        from datetime import datetime, timedelta

        start_time = time.time()
        start_datetime = datetime.now()
        last_checked_id = None
        logger.info("gmail.code_poll_started", timeout=timeout, poll_interval=5, sender_present=bool(sender),
                    console=f"Polling Gmail every 5s for verification code from {sender} (timeout: {timeout}s)...")
        while time.time() - start_time < timeout:
            elapsed = int(time.time() - start_time)
            try:
                if not self.imap:
                    self.connect()
                if not self.select_inbox():
                    raise GmailConnectionError("Could not select inbox")
                date_str = start_datetime.strftime("%d-%b-%Y")
                search_criteria = f'(FROM "{sender}" SINCE {date_str})'
                logger.info("gmail.searching", elapsed=elapsed, since=date_str, console=f"[{elapsed}s] Searching emails from {sender}...")
                _, messages = self.imap.search(None, search_criteria)
                email_ids = messages[0].split() if messages[0] else []
                logger.info("gmail.search_result", elapsed=elapsed, message_count=len(email_ids),
                              console=f'[{elapsed}s] Found {len(email_ids)} email(s) from {sender}')
                if email_ids:
                    latest_email_id = email_ids[-1]
                    if last_checked_id != latest_email_id:
                        email_subject = self.get_email_subject(latest_email_id)
                        logger.info("gmail.latest_message_found", elapsed=elapsed, message_id=_message_ref(latest_email_id), subject_length=len(email_subject),
                                      console=f"[{elapsed}s] Latest email subject decoded")
                        if email_subject:
                            try:
                                code = self.extract_verification_code_from_subject(email_subject)
                                logger.info("gmail.code_extracted", elapsed=elapsed, code_length=len(code),
                                            console=f"[{elapsed}s] Successfully extracted verification code")
                                return code
                            except VerificationCodeExtractionError:
                                logger.info("gmail.message_without_code", elapsed=elapsed,
                                              console=f"[{elapsed}s] Email found but no verification code in subject")
                                last_checked_id = latest_email_id
                time.sleep(5)
            except GmailConnectionError:
                logger.warning("gmail.reconnecting", elapsed=elapsed, console=f"[{elapsed}s] Gmail connection error, reconnecting...")
                try:
                    self.close()
                    self.connect()
                except:
                    time.sleep(10)
            except Exception as e:
                logger.error("gmail.poll_failed", elapsed=elapsed, error=str(e),
                             console=yellow(f"[{elapsed}s] Error while waiting for verification code: {e}"))
                time.sleep(5)
        raise GmailConnectionError(f"Timeout: No verification code received within {timeout} seconds")

    def close(self):
        """Close the IMAP connection"""
        try:
            if self.imap:
                try:
                    self.imap.close()
                finally:
                    try:
                        self.imap.logout()
                    finally:
                        self.imap = None
        except:
            pass

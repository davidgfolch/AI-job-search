from commonlib.observability import get_logger
from commonlib.terminalColor import yellow

logger = get_logger("scrapper.email_deleter")


def delete_email(imap, email_id: bytes) -> bool:
    """Delete a 2FA email after its code has been read, by flagging and expunging it"""
    message_id = email_id.decode() if isinstance(email_id, bytes) else str(email_id)
    try:
        imap.store(message_id, "+FLAGS", "\\Deleted")
        imap.expunge()
        logger.info("gmail.email_deleted", message_id=message_id, console="2FA email deleted")
        return True
    except Exception as e:
        logger.warning("gmail.email_delete_failed", message_id=message_id, error=str(e),
                       console=yellow(f"Failed to delete 2FA email {message_id}: {e}"))
        return False

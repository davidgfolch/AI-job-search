"""Re-exports of IP range and host target parsing from connection_manager."""
from commonlib.sql.connection_manager import _parse_ip_range, _parse_host_targets

__all__ = ["_parse_ip_range", "_parse_host_targets"]

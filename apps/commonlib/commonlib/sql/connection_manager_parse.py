"""Parsing of `COMMONLIB_DB_HOST` specs into concrete candidate hosts.

Leaf module (stdlib only) so both `connection_manager` and `db_hosts` can use it
without an import cycle.
"""
import ipaddress


def _parse_ip_range(range_str: str) -> list[str]:
    """Parse an IP range (start-end) into a list of IPs.
    Supports: 192.168.0.10-192.168.0.250, 192.168.0.10-250."""
    start_str, end_str = (x.strip() for x in range_str.split('-', 1))
    start_ip = ipaddress.IPv4Address(start_str)
    end_parts = end_str.split('.')
    if len(end_parts) < 4:
        start_parts = start_str.split('.')
        if len(end_parts) == 1:
            padded = start_parts[:3] + end_parts
        elif len(end_parts) == 2:
            padded = start_parts[:2] + end_parts
        elif len(end_parts) == 3:
            if end_parts[:2] == start_parts[:2]:
                padded = start_parts[:3] + [end_parts[2]]
            else:
                padded = [start_parts[0]] + end_parts
        end_str = '.'.join(padded)
    end_ip = ipaddress.IPv4Address(end_str)
    start_int = int(start_ip)
    end_int = int(end_ip)
    if end_int < start_int:
        raise ValueError(f"Range end {end_str} < start {start_str}")
    return [str(ipaddress.IPv4Address(i)) for i in range(start_int, end_int + 1)]


def _parse_host_targets(raw: str) -> list[str]:
    """Parse a host spec into a list of IPs.
    Supports: single IP, CIDR (192.168.1.0/24), range (10-250),
    comma-separated combinations."""
    targets = []
    for part in raw.split(','):
        part = part.strip()
        if not part:
            continue
        if '/' in part:
            try:
                network = ipaddress.IPv4Network(part, strict=False)
                targets.extend(str(ip) for ip in network.hosts())
            except ValueError:
                try:
                    targets.extend(_parse_ip_range(part.replace('/', '-', 1)))
                except Exception:
                    targets.append(part)
        elif '-' in part:
            try:
                targets.extend(_parse_ip_range(part))
            except Exception:
                targets.append(part)
        else:
            targets.append(part)
    return targets

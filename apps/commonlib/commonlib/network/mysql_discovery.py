import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

DEFAULT_MYSQL_PORT = 3306
SCAN_TIMEOUT = 0.5
MAX_WORKERS = 100
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'rootPass'
MYSQL_DATABASE = 'jobs'


def get_local_subnets():
    """Detect local LAN subnets by finding the machine's IP via UDP connect."""
    subnets = []
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(2)
    try:
        s.connect(('8.8.8.8', 80))
        parts = s.getsockname()[0].split('.')
        subnets.append(f"{parts[0]}.{parts[1]}.{parts[2]}.0/24")
        third = int(parts[2])
        for offset in [-1, 1]:
            adj = third + offset
            if 0 <= adj <= 255:
                subnets.append(f"{parts[0]}.{parts[1]}.{adj}.0/24")
    except Exception:
        pass
    finally:
        s.close()
    return subnets


def _scan_port(ip, port, timeout):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        return s.connect_ex((ip, port)) == 0
    except:
        return False
    finally:
        s.close()


def _scan_hosts(hosts, port, timeout):
    """Scan a list of hosts on the given port. Returns list of responsive IPs."""
    found = []
    print(f"Scanning {len(hosts)} hosts for MySQL on port {port}...", flush=True)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        fut_map = {ex.submit(_scan_port, h, port, timeout): h for h in hosts}
        for f in as_completed(fut_map):
            if f.result():
                found.append(fut_map[f])
    return found


def discover_mysql_hosts(subnets=None, targets=None, port=None, timeout=None):
    """Scan LAN for hosts with open MySQL port. Returns list of IPs.

    Args:
        subnets: List of CIDR subnets to scan (e.g. ['192.168.1.0/24']).
                 Ignored if targets is provided.
        targets: Specific list of IPs to scan.
        port: MySQL port (default 3306).
        timeout: Per-host scan timeout in seconds (default 0.5).
    """
    port = port or DEFAULT_MYSQL_PORT
    timeout = timeout or SCAN_TIMEOUT

    if targets is not None:
        print(f"Scanning targets: {', '.join(targets)} for MySQL on port {port}", flush=True)
        return _scan_hosts(targets, port, timeout)

    if subnets is None:
        subnets = get_local_subnets()

    found = []
    print(f"Scanning subnets: {', '.join(subnets)}", flush=True)
    for subnet_str in subnets:
        try:
            network = ipaddress.IPv4Network(subnet_str, strict=False)
        except Exception:
            continue
        hosts = [str(ip) for ip in network.hosts()]
        found.extend(_scan_hosts(hosts, port, timeout))
    return found


def verify_mysql(host, port=None, user=None, password=None, database=None):
    """Verify host is our MySQL — connect and check the database exists."""
    import mysql.connector
    port = port or DEFAULT_MYSQL_PORT
    user = user or MYSQL_USER
    password = password or MYSQL_PASSWORD
    database = database or MYSQL_DATABASE
    try:
        conn = mysql.connector.connect(
            host=host, port=port, user=user, password=password,
            database=database, connect_timeout=3
        )
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = %s",
            (database,)
        )
        exists = cursor.fetchone()[0] > 0
        cursor.close()
        conn.close()
        return exists
    except Exception:
        return False


def auto_discover_host():
    """Auto-discover MySQL host on LAN. Returns host IP string or None."""
    try:
        candidates = discover_mysql_hosts()
        if not candidates:
            return None
        for host in candidates:
            if verify_mysql(host):
                return host
        return None
    except Exception:
        return None

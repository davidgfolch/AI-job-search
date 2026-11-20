from pymongo import MongoClient
from pymongo.uri_parser import parse_uri

from commonlib.environmentUtil import getEnv
from commonlib.observability import get_logger
from commonlib.sql.mysqlUtil import get_read_connection

logger = get_logger("backend.repositories.dashboard_probe_repository")

MYSQL_QUERY = "SELECT 1"
MONGO_TIMEOUT_MS = 2000
MAX_ERROR_LENGTH = 200


class DashboardProbeRepository:
    """Read-only liveness probes for the datastores reported on the dashboard."""

    def probe_mysql(self) -> tuple[bool, str]:
        conn = None
        try:
            conn = get_read_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(MYSQL_QUERY)
                cursor.fetchall()
                return True, "SELECT 1 ok"
            finally:
                cursor.close()
        except Exception as e:
            logger.debug("datastore.probe_failed", error=str(e), source_module="mysql")
            return False, str(e)[:MAX_ERROR_LENGTH]
        finally:
            if conn is not None:
                try:
                    conn.consume_results()
                    conn.close()
                except Exception as e:
                    logger.debug("datastore.probe_close_failed", error=str(e), source_module="mysql")

    def probe_mongo(self, uri: str) -> tuple[bool, str]:
        client = None
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=MONGO_TIMEOUT_MS)
            client.admin.command("ping")
            return True, "ping ok"
        except Exception as e:
            logger.debug("datastore.probe_failed", error=str(e), source_module="mongo")
            return False, str(e)[:MAX_ERROR_LENGTH]
        finally:
            if client is not None:
                try:
                    client.close()
                except Exception as e:
                    logger.debug("datastore.probe_close_failed", error=str(e), source_module="mongo")

    @staticmethod
    def display_url(name: str, uri: str) -> str:
        """Show where a datastore lives without leaking credentials from MONGO_URI."""
        if name == "mongo":
            try:
                nodes = parse_uri(uri).get("nodelist", [])
                return "mongodb://" + ",".join(f"{host}:{port}" for host, port in nodes)
            except Exception:
                return "mongodb://<configured>"
        host = getEnv("COMMONLIB_DB_HOST", "mysql_db").strip() or "mysql_db"
        return f"mysql://{host}:3306"

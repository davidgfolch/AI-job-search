#!/usr/bin/env python3
"""Claude Code PreToolUse hook: require permission for database mutations.

The `jobs` MySQL database is live production data, so a write must never be the
agent's own initiative. Read-only SQL is always allowed; anything that pairs a
database client with a mutating statement, pipes a .sql file into a client, or
destroys a data volume is denied so the agent has to ask the user first.

Escapes the denial only when the command carries the AI_DB_WRITE_APPROVED token,
which the agent must add solely after the user approved that exact statement.
Mirrors .opencode/plugins/db-mutation.js behavior.

Reads the tool-use JSON from stdin. Exit 2 blocks the call and feeds stderr back.
"""
import json
import re
import sys

APPROVAL_TOKEN = "AI_DB_WRITE_APPROVED"

# The client binary, not the compose service name: `\b` does not match the
# `mysql` inside `mysql_db` (underscore is a word char) but does match the tail
# of the container name `ai-job-search-mysql`, which is what we want.
CLIENT = re.compile(
    r"\b(?:mysql|mariadb|psql|pgcli|sqlcmd|sqlite3?|mongosh|mongo|clickhouse-client|cockroach|redis-cli)\b",
    re.IGNORECASE,
)

# Data, schema, and privilege mutations. Maintenance verbs (flush/lock/optimize/
# repair) are intentionally excluded: they do not change stored data.
MUTATION = re.compile(
    r"\b(?:insert|update|delete|replace|drop|truncate|alter|create|rename|grant|revoke"
    r"|merge|upsert|call|outfile|dumpfile)\b|\bload\s+(?:data|xml)\b",
    re.IGNORECASE,
)

# A .sql file handed to a client: `mysql < x.sql`, `psql -f x.sql`, `source x.sql`.
SQL_FILE = re.compile(r"(?:<\s*[\"']?[\w./\\-]+\.sql\b|--file[= ][^\s]+\.sql\b|\bsource\s+[\w./\\-]+\.sql\b)", re.IGNORECASE)

# Destroying the database by removing its volume.
VOLUME_WIPE = re.compile(
    r"\bdocker(?:-|\s+)compose\b[^\n]*\bdown\b[^\n]*(?:-v\b|--volumes\b)"
    r"|\bdocker\s+volume\s+(?:rm|prune)\b"
    r"|\bdocker\s+system\s+prune\b[^\n]*(?:--volumes\b|\s-v\b)"
    r"|\bdocker\s+(?:container|image)\s+rm\b[^\n]*--volumes\b",
    re.IGNORECASE,
)

# Document-store and key-value writes. `MUTATION` misses camelCase verbs such as
# `updateMany`, so these are matched explicitly, and only when the command really
# invokes that kind of client (a container named `...-mongo` is not a client).
MONGO_CLIENT = re.compile(r"\b(?:mongosh|mongo)\b", re.IGNORECASE)
MONGO_MUTATION = re.compile(
    r"\b(?:deletemany|deleteone|dropdatabase|updatemany|updateone|insertmany|insertone|bulkwrite"
    r"|replaceone|findoneand\w*)\b|\bdrop\s*\(|\bremove\s*\(",
    re.IGNORECASE,
)
REDIS_CLIENT = re.compile(r"\bredis-cli\b", re.IGNORECASE)
REDIS_MUTATION = re.compile(
    r"\b(?:flushall|flushdb|del|set|setex|setnx|hset|hmset|lpush|rpush|sadd|zadd|xadd|expire"
    r"|persist|eval|evalsha|script|save|bgsave)\b",
    re.IGNORECASE,
)

# A Python/Node one-liner that drives the repo data layer with a mutating
# statement. Narrow on purpose: both halves must be present.
CODE_MUTATION = re.compile(
    r"\b(?:sqlUtil|mysqlUtil|aiEnrichRepository|query_executor|session\.execute|conn(?:ection)?\.execute"
    r"|cursor\.execute|db\.collection|create_engine|deleteMany|updateMany|bulkWrite|flushall|flushdb)\b",
    re.IGNORECASE,
)


def find_violation(command: str) -> str | None:
    if APPROVAL_TOKEN in command:
        return None
    if not command.strip():
        return None
    if VOLUME_WIPE.search(command):
        return "it destroys a database/data volume (docker volume removal or `down -v`)"
    if CODE_MUTATION.search(command) and MUTATION.search(command):
        return "it pairs a data-layer call with a mutating SQL statement"
    if MONGO_CLIENT.search(command) and MONGO_MUTATION.search(command):
        return "it pairs a mongo client with a mutating operation"
    if REDIS_CLIENT.search(command) and REDIS_MUTATION.search(command):
        return "it pairs a redis client with a mutating command"
    if CLIENT.search(command):
        if SQL_FILE.search(command):
            return "it pipes a .sql file into a database client, whose contents cannot be reviewed"
        if MUTATION.search(command):
            return "it pairs a database client with a mutating SQL statement"
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0

    if payload.get("tool_name", "") != "Bash":
        return 0

    command = (payload.get("tool_input", {}) or {}).get("command") or ""
    reason = find_violation(command if isinstance(command, str) else "")
    if not reason:
        return 0

    print(
        f"BLOCKED by .claude/rules/db-mutation-permission.md: {reason}.\n"
        "The `jobs` MySQL database is live production data, so a write needs the user's explicit "
        "permission first. Do this instead: run read-only SELECT/SHOW/EXPLAIN to measure the current "
        "state, then ask the user to approve the exact statement and the expected row count, and wait "
        f"for a yes. Once approved, re-run it with the {APPROVAL_TOKEN} token in the command.\n"
        f"Offending command: {command}",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())

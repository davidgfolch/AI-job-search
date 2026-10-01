// db-mutation OpenCode plugin
// Requires the user's explicit permission before any database mutation runs.
//
// The `jobs` MySQL database is live production data, so a write must never be the
// agent's own initiative. Read-only SQL is always allowed; anything that pairs a
// database client with a mutating statement, pipes a .sql file into a client, or
// destroys a data volume throws and aborts the call.
//
// Escapes the denial only when the command carries the AI_DB_WRITE_APPROVED token,
// which the agent must add solely after the user approved that exact statement.
// Mirrors .claude/hooks/db-mutation.py behavior; the canonical policy lives in
// .claude/rules/db-mutation-permission.md.
const APPROVAL_TOKEN = "AI_DB_WRITE_APPROVED";

// The client binary, not the compose service name: `\b` does not match the
// `mysql` inside `mysql_db` (underscore is a word char) but does match the tail
// of the container name `ai-job-search-mysql`, which is what we want.
const CLIENT =
  /\b(?:mysql|mariadb|psql|pgcli|sqlcmd|sqlite3?|mongosh|mongo|clickhouse-client|cockroach|redis-cli)\b/i;

// Data, schema, and privilege mutations. Maintenance verbs (flush/lock/optimize/
// repair) are intentionally excluded: they do not change stored data.
const MUTATION =
  /\b(?:insert|update|delete|replace|drop|truncate|alter|create|rename|grant|revoke|merge|upsert|call|outfile|dumpfile)\b|\bload\s+(?:data|xml)\b/i;

// A .sql file handed to a client: `mysql < x.sql`, `psql -f x.sql`, `source x.sql`.
const SQL_FILE =
  /(?:<\s*["']?[\w./\\-]+\.sql\b|--file[= ][^\s]+\.sql\b|\bsource\s+[\w./\\-]+\.sql\b)/i;

// Destroying the database by removing its volume.
const VOLUME_WIPE =
  /\bdocker(?:-|\s+)compose\b[^\n]*\bdown\b[^\n]*(?:-v\b|--volumes\b)|\bdocker\s+volume\s+(?:rm|prune)\b|\bdocker\s+system\s+prune\b[^\n]*(?:--volumes\b|\s-v\b)|\bdocker\s+(?:container|image)\s+rm\b[^\n]*--volumes\b/i;

// Document-store and key-value writes. `MUTATION` misses camelCase verbs such as
// `updateMany`, so these are matched explicitly, and only when the command really
// invokes that kind of client (a container named `...-mongo` is not a client).
const MONGO_CLIENT = /\b(?:mongosh|mongo)\b/i;
const MONGO_MUTATION =
  /\b(?:deletemany|deleteone|dropdatabase|updatemany|updateone|insertmany|insertone|bulkwrite|replaceone|findoneand\w*)\b|\bdrop\s*\(|\bremove\s*\(/i;
const REDIS_CLIENT = /\bredis-cli\b/i;
const REDIS_MUTATION =
  /\b(?:flushall|flushdb|del|set|setex|setnx|hset|hmset|lpush|rpush|sadd|zadd|xadd|expire|persist|eval|evalsha|script|save|bgsave)\b/i;

// A Python/Node one-liner that drives the repo data layer with a mutating
// statement. Narrow on purpose: both halves must be present.
const CODE_MUTATION =
  /\b(?:sqlUtil|mysqlUtil|aiEnrichRepository|query_executor|session\.execute|conn(?:ection)?\.execute|cursor\.execute|db\.collection|create_engine|deleteMany|updateMany|bulkWrite|flushall|flushdb)\b/i;

function findViolation(command) {
  if (!command || !command.trim()) return null;
  if (command.includes(APPROVAL_TOKEN)) return null;
  if (VOLUME_WIPE.test(command))
    return "it destroys a database/data volume (docker volume removal or `down -v`)";
  if (CODE_MUTATION.test(command) && MUTATION.test(command))
    return "it pairs a data-layer call with a mutating SQL statement";
  if (MONGO_CLIENT.test(command) && MONGO_MUTATION.test(command))
    return "it pairs a mongo client with a mutating operation";
  if (REDIS_CLIENT.test(command) && REDIS_MUTATION.test(command))
    return "it pairs a redis client with a mutating command";
  if (CLIENT.test(command)) {
    if (SQL_FILE.test(command))
      return "it pipes a .sql file into a database client, whose contents cannot be reviewed";
    if (MUTATION.test(command))
      return "it pairs a database client with a mutating SQL statement";
  }
  return null;
}

export const DbMutationPlugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "bash") return;
      const command = (output.args || {}).command;
      const reason = findViolation(command);
      if (!reason) return;
      throw new Error(
        `BLOCKED by .claude/rules/db-mutation-permission.md: ${reason}. ` +
          "The `jobs` MySQL database is live production data, so a write needs the user's explicit " +
          "permission first. Do this instead: run read-only SELECT/SHOW/EXPLAIN to measure the current " +
          "state, then ask the user to approve the exact statement and the expected row count, and wait " +
          `for a yes. Once approved, re-run it with the ${APPROVAL_TOKEN} token in the command.\n` +
          `Offending command: ${command}`,
      );
    },
  };
};

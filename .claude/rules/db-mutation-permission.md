---
trigger: always_on
---

## Database changes require explicit user permission

**Never execute a data or schema mutation against a project database on your own initiative.** The `jobs` MySQL database is live production data: scraping, enrichment, applications, and manual curation all write to it continuously. Ask the user first, every time, and wait for an explicit "yes" before running anything that writes.

This applies to the running stack (`ai-job-search-mysql`, `ai-job-search-mongo_db`) **and** to any other database you touch while working on this repo, including the `dependabot-test` sandbox clone and a locally started `mysql_db`.

### Blocked without permission

| Category | Examples |
|----------|----------|
| Row mutations | `INSERT`, `UPDATE`, `DELETE`, `REPLACE`, `MERGE`, `UPSERT`, `LOAD DATA`, `SELECT ... INTO OUTFILE` |
| Schema / objects | `CREATE`, `ALTER`, `DROP`, `TRUNCATE`, `RENAME` |
| Privileges | `GRANT`, `REVOKE` |
| Stored code | `CALL` to a procedure that writes |
| Bulk replay | piping or sourcing a `.sql` file into a client (`mysql < x.sql`, `source x.sql`, `psql -f x.sql`) |
| Data destruction | `docker compose down -v` / `--volumes`, `docker volume rm`, `docker system prune --volumes`, deleting `data/` |

Mongo equivalents (`deleteMany`, `drop`, `updateMany`, `bulkWrite`) and Redis writes (`SET`, `DEL`, `FLUSHALL`, `FLUSHDB`) are blocked the same way.

### Allowed without permission

Read-only access is fine and expected — use it constantly to verify claims:

- `SELECT`, `SHOW`, `DESCRIBE`, `EXPLAIN`, `COUNT`, `WITH ... SELECT`
- Reading container logs, metrics, or `.env`
- `SELECT ROW_COUNT()` and similar diagnostics
- `docker compose restart` / `up` / `logs` / `ps` (no data loss)

When unsure whether a statement writes, treat it as blocked.

### How to run an approved mutation

Only after the user has explicitly approved, include the token `AI_DB_WRITE_APPROVED` in the command so the guardrail lets it through:

```bash
# bash
AI_DB_WRITE_APPROVED=1 docker exec ai-job-search-mysql mysql -uroot -prootPass jobs -e "UPDATE ..."
```

```powershell
# PowerShell
$env:AI_DB_WRITE_APPROVED=1; docker exec ai-job-search-mysql mysql -uroot -prootPass jobs -e "UPDATE ..."
```

State the exact statement and the expected row count in your question, and re-confirm if the scope grows (e.g. the first approval covered 100 rows, not 6000). Never add the token to a command the user has not approved.

### Ask like this

Report the current state first (read-only), then ask. Example:

> The backfill reset would set `ai_enriched=NULL` on **5653** rows (`created >= '2026-09-18'`, not ignored/discarded/closed) so the worker reprocesses them with `repeat_penalty=1.0`. This writes to the live `jobs` table. Shall I run it?

Do not run the write in the same turn as the question.

### Enforcement

A `PreToolUse` guardrail blocks these commands before they execute, so this is not a memory task:

| Mechanism | Harness | Behavior |
|-----------|---------|----------|
| `.claude/rules/db-mutation-permission.md` | all | This rule (the canonical policy) |
| `.claude/hooks/db-mutation.py` | Claude Code (`PreToolUse` on `Bash`) | Exits 2 and denies the call, with the reason on stderr |
| `.opencode/plugins/db-mutation.js` | opencode | Throws and aborts the `bash` call with the same reason |

Limitations to be honest about: the guardrail matches database clients, SQL keywords, and destructive Docker volume commands. It cannot see inside an arbitrary Python/Node script that builds SQL dynamically, and it cannot verify that the user actually consented — only you can. When a mutation is genuinely warranted and the guardrail is bypassed, say so explicitly in your summary.

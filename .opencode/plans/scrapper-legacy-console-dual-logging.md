# Restore the scrapper console while keeping structured records

Status: completed

## Problem

`.opencode/plans/structured-logging-normalization.md` (commit `da0a184`) replaced the
scrapper's 219 `print()` calls across 34 files with structlog records. The JSONL
contract was the goal, but the console was a side effect: in the default
`CONSOLE_RECORD` mode the terminal now shows rendered records
(`2026-09-29 13:00:00 [info     ] linkedin.job.inserted job_id=42 insert_id=99`) instead
of the transcript an operator reads while a scrape runs, and progress prefixes that
used to run together on one line (`pg 1 job 1 - 42, Python Dev - INSERTED 99!`) became
one line per event. Operators also lost the shared `commonlib` filtering that used to
keep library chatter out of the scraper's output.

## Solution

Split the two halves of a record instead of choosing one.

1. **`commonlib.console_render`** (new): `split_console_text()` moves the `console=`
   text into the record's `message` (ANSI-stripped) and `end=` into a private
   `_console_end`; `render_console()` prints it. `log_writer.public_record()` drops the
   private keys so the file never carries the terminator.
2. **Two modes**, resolved per record so an entrypoint can select one after a shared
   module already logged at import time: `CONSOLE_RECORD` (default, unchanged for every
   other app) and `CONSOLE_MESSAGE`. A record without `console=` is file-only and
   silent, which is what mutes the imported `commonlib` chatter.
3. **Scrapper restore**: every call site that printed before `da0a184` got its old text
   back as `console=`, with `end=""` where the old code used `print(..., end='')`.
   `main.py` selects `CONSOLE_MESSAGE`.
4. **Levels**: the console only shows what survives `LOG_LEVEL=20`, so the former
   unconditional prints are logged at `info`; genuinely debug-gated output stays
   `debug`.
5. **Redaction**: console text is a log line, so it obeys the same rules. URL query
   strings (`baseNavigator`, `executor_factory`), OTP codes (Indeed, Indeed/Glassdoor
   Gmail, Glassdoor) and email subjects are dropped, and `LinkedinService` prints
   `HTML_LENGTH` / `MARKDOWN_LENGTH` instead of the documents.
6. **Log file announced at startup**: `main()` logs `logging.file_opened` with the
   absolute `path` of the JSONL file it is about to write, as the first console line.

## Outcome

`bash scripts/test.sh commonlib scrapper` → 730 passed, 1 skipped (commonlib), 565
passed (scrapper).

Verified against a replay of a real row loop: the console reproduces the pre-`da0a184`
transcript, including the assembled one-line progress output, and `scrapper.jsonl`
contains one record per event with ANSI-stripped `message` values. A record such as
`sql.query_executed` appears in the file and not on the console.

## Follow-ups

- `LOG_CONSOLE_MODE` only applies to apps that do not hard-code a mode; the scrapper
  always runs in `CONSOLE_MESSAGE`.
- `LinkedinService.print_job` now prints lengths rather than the job document, so the
  old HTML/markdown dump is gone from the console by design.
- `env.loaded` and `scrapper_config`'s `config.loaded` are emitted while
  `scrapper.core` is imported, which is before `main.py` selects the console mode, so
  those two still render as records on stdout. Moving the mode selection into
  `scrapper/__init__.py` would silence them for every entrypoint; left out because it
  makes importing the package configure global logging.

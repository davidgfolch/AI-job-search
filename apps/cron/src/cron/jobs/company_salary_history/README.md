# Company Salary History Scanner

Background cron job that tracks salary changes for jobs over time and stores aggregated company-level salary history in MongoDB.

## Purpose

Job offers on platforms like LinkedIn, Infojobs, etc. update their salary fields. This scanner detects those changes and builds a time-series record of salary-by-company data, which is then exposed via the backend API and displayed in the Web UI (inline indicator + popup modal).

## How it works

The scanner runs in two phases per tick:

### 1. New job backfill (`_fetch_jobs`)

Queries MySQL for jobs where `salary IS NOT NULL` and `id > last_job_id` (incremental cursor stored in `cron_state`). For each batch, it normalizes the company name and inserts records into MongoDB's `company_salary_history` collection.

### 2. Updated job detection (`_fetch_updated`)

Queries MySQL for jobs with `modified > last_run_at` that were already processed (id ≤ last_job_id). For each one, it compares the current salary against the last recorded salary in MongoDB. If different, a new record is inserted. This catches:

- Salary changes on existing jobs
- Jobs that had no salary during backfill but later got salary from AI enrichment (`aiEnrich` apps)

## State tracking

Job state is persisted in MongoDB's `cron_state` collection:

```json
{
  "_id": "companySalaryHistory",
  "last_job_id": 12345,
  "last_run_at": "2026-06-09T18:00:00",
  "status": "ok"
}
```

## Data model

Records stored in `company_salary_history` collection:

```json
{
  "job_id": 12345,
  "company_raw": "Experis IT",
  "company_normalized": "experis it",
  "title": "Software Engineer",
  "salary": "33.000€ - 36.000€ Bruto/año",
  "recorded_at": "2026-06-09T18:00:00",
  "source": "backfill"
}
```

## Duplicate prevention

A unique compound index on `{job_id, salary, recorded_at}` prevents exact duplicates. `save_records` uses `insert_many(ordered=False)` and gracefully handles duplicate key errors.

## Company name matching

Queries use regex prefix matching on the first word of the normalized name (e.g., `^experis` matches "experis", "experis it", "experis espaa"). See `commonlib/company_normalizer.py`.

## Configuration

See [`apps/cron/README.md`](../../../README.md) for `CRON_SALARY_CADENCY` and MongoDB settings.

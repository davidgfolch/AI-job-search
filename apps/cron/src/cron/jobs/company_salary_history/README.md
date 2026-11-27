# Company Salary History Scanner

Background cron job that tracks salary changes for jobs over time and stores aggregated company-level salary history in MongoDB.

## Purpose

Job offers on platforms like LinkedIn, Infojobs, etc. update their salary fields. This scanner detects those changes and builds a time-series record of salary-by-company data, which is then exposed via the backend API and displayed in the Web UI (inline indicator + popup modal).

## Behaviour

The scanner backfills jobs that already have a salary and then detects later changes, including salaries added by AI enrichment.
Company names are normalized so variants group together. Progress and recorded salary history are stored in MongoDB; see [scanner.py](scanner.py) for details.

## Configuration

See [`apps/cron/README.md`](../../../../README.md) for `CRON_SALARY_CADENCY` and MongoDB settings.

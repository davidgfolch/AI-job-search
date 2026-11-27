#!/usr/bin/env python3
"""Report scrapper keyword totals and already-in-DB duplicates from the JSONL logs."""
import argparse
import csv
from datetime import date, timedelta
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "apps" / "commonlib" / "commonlib" / "keyword_stats.py"
_spec = spec_from_file_location("keyword_stats", MODULE_PATH)
_module = module_from_spec(_spec)
_spec.loader.exec_module(_module)
aggregate, has_rotated_history, read_events = _module.aggregate, _module.has_rotated_history, _module.read_events

DEFAULT_LOG_DIR = ROOT / "apps" / "scrapper" / "data" / "logs"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-dir", default=str(DEFAULT_LOG_DIR), help="directory holding scrapper.jsonl*")
    parser.add_argument("--site", help="only this site (e.g. Indeed)")
    parser.add_argument("--keyword", help="only keywords containing this text")
    parser.add_argument("--date", dest="only_date", help="single scrape date YYYY-MM-DD")
    parser.add_argument("--days", type=int, default=30, help="days to include when --date is absent")
    parser.add_argument("--max-ids", type=int, default=20, help="maximum duplicate ids listed per row")
    parser.add_argument("--csv", help="also write the report to this CSV path")
    return parser.parse_args()


def main():
    args = parse_args()
    end = date.fromisoformat(args.only_date) if args.only_date else date.today()
    start = end if args.only_date else end - timedelta(days=args.days - 1)
    rows = aggregate(read_events(args.log_dir, str(start), str(end)), max_ids=args.max_ids, site=args.site, keyword=args.keyword)
    headers = ["date", "site", "keyword", "reported", "processed", "new", "dupes", "duplicate_ids"]
    table = [[row.date, row.site, row.keyword, row.reported_total, row.processed, row.new, row.duplicates, ", ".join(str(job_id) for job_id in row.duplicate_ids)] for row in rows]
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)
            writer.writerows(table)
    widths = [max([len(header)] + [len(str(row[index])) for row in table]) for index, header in enumerate(headers)]
    print("  ".join(header.ljust(width) for header, width in zip(headers, widths, strict=False)))
    for row in table:
        print("  ".join(str(cell).ljust(width) for cell, width in zip(row, widths, strict=False)))
    if has_rotated_history(args.log_dir):
        print("note: all log rotation slots are in use, older dates may be unavailable")


if __name__ == "__main__":
    main()

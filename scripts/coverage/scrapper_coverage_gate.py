#!/usr/bin/env python
"""Gate scrapper coverage on production statements and lines.

coverage.py's fail_under only understands the branch-inclusive total, which the project
does not gate on: branches and functions are reported for information only. This script
reads coverage.xml, drops test files from the denominator (they live inside the package)
and fails when production statements or lines fall below the threshold.

Usage:
    python scripts/coverage/scrapper_coverage_gate.py [--min 90] [--xml apps/scrapper/coverage.xml] [--worst 20]
"""

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

TEST_PATH_PARTS = ("test", "tests")
TEST_FILE_SUFFIXES = ("_test.py", "conftest.py")


def _is_production(filename: str) -> bool:
    normalized = filename.replace("\\", "/")
    parts = normalized.split("/")
    if any(part in TEST_PATH_PARTS for part in parts[:-1]):
        return False
    return not normalized.endswith(TEST_FILE_SUFFIXES)


def read_coverage(xml_path: Path) -> list[tuple[str, int, int]]:
    root = ET.parse(xml_path).getroot()
    files = []
    for cls in root.iter("class"):
        filename = cls.get("filename") or ""
        if not _is_production(filename):
            continue
        total = 0
        covered = 0
        for line in cls.iter("line"):
            total += 1
            if int(line.get("hits") or 0) > 0:
                covered += 1
        files.append((filename, covered, total))
    return files


def _pct(covered: int, total: int) -> float:
    return 100.0 * covered / total if total else 100.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min", type=float, default=90.0, help="minimum percentage for statements and lines")
    parser.add_argument("--xml", default="apps/scrapper/coverage.xml", help="path to coverage.xml")
    parser.add_argument("--worst", type=int, default=20, help="how many least-covered files to report")
    args = parser.parse_args()

    xml_path = Path(args.xml)
    if not xml_path.is_file():
        print(f"scrapper_coverage_gate: {xml_path} not found; run the coverage suite first")
        return 1

    files = read_coverage(xml_path)
    if not files:
        print(f"scrapper_coverage_gate: no production files measured in {xml_path}")
        return 1

    statements_total = sum(total for _, _, total in files)
    statements_covered = sum(covered for _, covered, _ in files)
    statements_pct = _pct(statements_covered, statements_total)

    failures = []
    if statements_pct + 1e-9 < args.min:
        failures.append("statements")
    missing = int(-(-statements_total * args.min // 100)) - statements_covered
    if missing > 0:
        failures.append(f"statements short by {missing}")

    print(f"scrapper_coverage_gate: statements {statements_covered}/{statements_total} = {statements_pct:.2f}% (min {args.min:.2f}%)")
    if args.worst > 0:
        print("least covered production files:")
        for filename, covered, total in sorted(files, key=lambda item: (_pct(item[1], item[2]), -item[2]))[: args.worst]:
            print(f"  {_pct(covered, total):6.2f}%  {total - covered:4d} missing  {filename}")

    if failures:
        print(f"scrapper_coverage_gate: FAILED ({'; '.join(failures)})")
        return 1
    print("scrapper_coverage_gate: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""Filter external dependency nodes from a graphify graph.

Removes nodes that represent third-party package references
(pkg_*, ref_* patterns from pyproject.toml/package.json) and
bare package-name nodes.

Usage:
    python scripts/graphify/graphify-filter-deps.py [--graph PATH]
"""
import json
import sys
import re
from pathlib import Path


EXTERNAL_DEP_PATTERNS = re.compile(
    r'(^|::)(pkg_|ref_)'
)

BARE_PACKAGE_NAMES = {
    'aiCvMatcher', 'aiEnrich', 'aiEnrich3', 'aiEnrichNew', 'aiEnrichSkill',
    'aiFormFiller', 'backend', 'commonlib', 'cron', 'scrapper', 'web',
}


def is_external_dep(node: dict) -> bool:
    nid = node.get("id", "")
    label = node.get("label", "")
    source_file = node.get("source_file", "")
    # Match pkg_* or ref_* patterns anywhere in the ID
    if EXTERNAL_DEP_PATTERNS.search(nid):
        return True
    if EXTERNAL_DEP_PATTERNS.search(label):
        return True
    # Match bare package nodes (from pyproject.toml name field)
    if label in BARE_PACKAGE_NAMES or nid in BARE_PACKAGE_NAMES:
        return True
    # Match nodes from package.json dependency sections
    if source_file and source_file.endswith('package.json'):
        return True
    # Match manifest.json
    if source_file and source_file.endswith('manifest.json'):
        return True
    return False


def filter_deps(graph_path: Path) -> int:
    data = json.loads(graph_path.read_text(encoding="utf-8"))
    nodes = data.get("nodes", [])
    links = data.get("links", [])

    before = len(nodes)
    dep_ids = set()
    kept_nodes = []
    for n in nodes:
        if is_external_dep(n):
            dep_ids.add(n.get("id", ""))
        else:
            kept_nodes.append(n)

    kept_links = [e for e in links
                  if e.get("source", "") not in dep_ids
                  and e.get("target", "") not in dep_ids]

    data["nodes"] = kept_nodes
    data["links"] = kept_links
    graph_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    removed = before - len(kept_nodes)
    return removed


def main():
    graph_path = Path("graphify-out/graph.json")
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--graph" and i + 1 < len(args):
            graph_path = Path(args[i + 1])
            i += 2
        else:
            i += 1
    if not graph_path.exists():
        print(f"ERROR: graph not found: {graph_path}", file=sys.stderr)
        sys.exit(1)
    print(f"Filtering external dependencies from {graph_path}...")
    removed = filter_deps(graph_path)
    print(f"Removed {removed} external dependency node(s)")


if __name__ == "__main__":
    main()

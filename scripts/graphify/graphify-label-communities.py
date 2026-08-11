#!/usr/bin/env python3
"""Deterministic community labeling for graphify graphs (no LLM needed).

Reads graphify-out/graph.json, generates semantic community names
based on the dominant module + top node labels, and writes
graphify-out/.graphify_labels.json for graphify to consume.

Usage:
    python scripts/graphify-label-communities.py [--graph PATH]
"""
import json
import sys
import re
from pathlib import Path
from collections import Counter


NON_SEMANTIC_PATTERNS = re.compile(
    r'(__init__|pyproject\.toml|package\.json|tsconfig\.json|'
    r'poetry\.toml|\.gitignore|Dockerfile|'
    r'run\.(sh|bat)|pytest|unittest_mock|ref_|pkg_|'
    r'^devDependencies$|^dependencies$|^scripts$|'
    r'^compilerOptions$|^typescript-eslint$|'
    r'^(fixture|parametrize|patch|conv_save|conv_remove|conv_append|'
    r'\.navigator\(\)|\.service\(\)|\.mock_selenium\(\)|\.authenticator\(\)|'
    r'\.test_job_exists_in_db\(\))$)'
)


def _skip_label(label: str) -> bool:
    if not label:
        return True
    label = str(label)
    if NON_SEMANTIC_PATTERNS.search(label):
        return True
    if label.endswith(('_test.py', '_test.ts', '.test.ts', '.test.tsx', '.test.js')):
        return True
    return False


def generate_labels(graph_path: Path) -> dict:
    data = json.loads(graph_path.read_text(encoding="utf-8"))
    nodes = data.get("nodes", [])
    links = data.get("links", [])
    degree = Counter()
    for e in links:
        degree[e.get("source", "")] += 1
        degree[e.get("target", "")] += 1
    node_map = {}
    for n in nodes:
        nid = n.get("id", "")
        node_map[nid] = n
    communities: dict[int, list[dict]] = {}
    for n in nodes:
        cid = n.get("community")
        if cid is not None:
            communities.setdefault(cid, []).append(n)
    labels = {}
    seen_module_labels = Counter()
    for cid in sorted(communities.keys()):
        comm_nodes = communities[cid]
        repos = Counter()
        for n in comm_nodes:
            repos[n.get("repo", "unknown")] += 1
        if not repos:
            labels[str(cid)] = f"Community {cid}"
            continue
        top_repo = repos.most_common(1)[0][0]
        top_repo_label = top_repo if top_repo != "unknown" else "misc"
        scored = []
        for n in comm_nodes:
            nid = n.get("id", "")
            label = n.get("label", "") or nid.split("::", 1)[-1] if "::" in nid else nid
            deg = degree.get(nid, 0)
            if _skip_label(label):
                continue
            scored.append((deg, label, nid))
        if scored:
            scored.sort(reverse=True)
            best_label = scored[0][1]
        else:
            parts = set()
            for n in comm_nodes:
                sf = n.get("source_file", "") or n.get("id", "").split("::", 1)[-1]
                base = Path(sf).stem if sf else ""
                if base == '__init__':
                    p = Path(sf).parent
                    if p.name == 'test' and p.parent.name:
                        base = f"{p.parent.name}_test"
                    else:
                        base = p.name
                if base and not _skip_label(base):
                    parts.add(base)
            best_label = next(iter(sorted(parts))) if parts else f"community_{cid}"
        # Ensure uniqueness by appending module prefix
        candidate = f"{top_repo_label}::{best_label}"
        labels[str(cid)] = candidate
    return labels


def main():
    graph_path = Path("graphify-out/graph.json")
    labels_path = Path("graphify-out/.graphify_labels.json")
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
    print(f"Generating community labels for {graph_path}...")
    labels = generate_labels(graph_path)
    labels_path.write_text(json.dumps(labels, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(labels)} labels to {labels_path}")
    for cid in sorted(labels.keys(), key=int):
        print(f"  Community {cid}: {labels[cid]}")


if __name__ == "__main__":
    main()

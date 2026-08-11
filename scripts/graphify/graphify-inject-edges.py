#!/usr/bin/env python3
"""Inject cross-module edges into a merged graphify graph.

Reads graphify-out/graph.json (merged) and graphify-out/cross-module-edges.json,
adds one edge between the highest-degree node of each module pair, and writes back.

Usage:
    python scripts/graphify/graphify-inject-edges.py [--graph PATH] [--edges PATH]
"""
import json
import sys
from pathlib import Path

try:
    import networkx as nx
    from networkx.readwrite import json_graph
except ImportError:
    print("ERROR: networkx is required. Install with: pip install networkx", file=sys.stderr)
    sys.exit(1)


def load_graph(path: Path) -> nx.Graph:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "links" not in data and "edges" in data:
        data = dict(data, links=data["edges"])
    try:
        return json_graph.node_link_graph(data, edges="links")
    except TypeError:
        return json_graph.node_link_graph(data)


def save_graph(G: nx.Graph, path: Path) -> None:
    data = json_graph.node_link_data(G, edges="links")
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _belongs_to_module(G: nx.Graph, node: str, repo_tag: str) -> bool:
    """Check if a node belongs to a module by repo attribute or ID prefix."""
    if G.nodes[node].get("repo") == repo_tag:
        return True
    prefix = f"{repo_tag}::"
    if isinstance(node, str) and node.startswith(prefix):
        return True
    return False


def find_representative_node(G: nx.Graph, repo_tag: str) -> str | None:
    """Find the highest-degree node belonging to a given repo module."""
    candidates = [(G.degree(n), n) for n in G.nodes if _belongs_to_module(G, n, repo_tag)]
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def inject_edges(graph_path: Path, edges_path: Path) -> int:
    G = load_graph(graph_path)
    edges_def = json.loads(edges_path.read_text(encoding="utf-8"))
    injected = 0
    for edge in edges_def.get("edges", []):
        src_repo = edge["from"]
        tgt_repo = edge["to"]
        relation = edge.get("relation", "depends_on")
        src_node = find_representative_node(G, src_repo)
        tgt_node = find_representative_node(G, tgt_repo)
        if not src_node:
            print(f"  SKIP: no nodes found for module '{src_repo}'")
            continue
        if not tgt_node:
            print(f"  SKIP: no nodes found for module '{tgt_repo}'")
            continue
        if G.has_edge(src_node, tgt_node):
            print(f"  SKIP: edge already exists {src_repo} -> {tgt_repo}")
            continue
        G.add_edge(src_node, tgt_node, relation=relation, confidence="INFERRED", source="cross-module-edges")
        injected += 1
        print(f"  ADDED: {src_repo} -> {tgt_repo} ({relation})")
    save_graph(G, graph_path)
    return injected


def main():
    graph_path = Path("graphify-out/graph.json")
    edges_path = Path("graphify-out/cross-module-edges.json")
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--graph" and i + 1 < len(args):
            graph_path = Path(args[i + 1])
            i += 2
        elif args[i] == "--edges" and i + 1 < len(args):
            edges_path = Path(args[i + 1])
            i += 2
        else:
            i += 1
    if not graph_path.exists():
        print(f"ERROR: graph not found: {graph_path}", file=sys.stderr)
        sys.exit(1)
    if not edges_path.exists():
        print(f"ERROR: edges definition not found: {edges_path}", file=sys.stderr)
        sys.exit(1)
    print(f"Injecting cross-module edges into {graph_path}...")
    count = inject_edges(graph_path, edges_path)
    print(f"Injected {count} cross-module edge(s)")


if __name__ == "__main__":
    main()

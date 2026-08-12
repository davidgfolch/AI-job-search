#!/usr/bin/env python3
"""Build vis-network datasets from a raw merged graphify graph.

The raw graph (graph.raw.json, preserved right after merge-graphs) has no
communities, so nodes are colored by module (repo) and rendered force-directed.
"""
import html as _html
import json
from collections import Counter
from pathlib import Path

def js_safe(obj) -> str:
    """Escape </script> sequences so embedded JSON cannot break out of the script tag."""
    return json.dumps(obj).replace("</", "<\\/")

def sanitize(value) -> str:
    return _html.escape(str(value or ""))

def load_graph(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    return dict(data, links=data["links"] if "links" in data else data.get("edges", []))

def build_raw_vis(data: dict, module_hex: dict[str, str]) -> tuple[list[dict], list[dict]]:
    nodes, links = data.get("nodes", []), data.get("links", [])
    degree = Counter()
    for e in links:
        degree[e.get("source", "")] += 1
        degree[e.get("target", "")] += 1
    max_deg = max(degree.values(), default=1) or 1
    vis_nodes = []
    for n in nodes:
        nid = n["id"]
        mod = n.get("repo", "")
        label = sanitize(n.get("label", nid))
        deg = degree.get(nid, 1)
        color = module_hex.get(mod, "#77778a")
        vis_nodes.append({
            "id": nid, "label": label,
            "color": {"background": color, "border": color, "highlight": {"background": "#ffffff", "border": color}},
            "size": round(8 + 16 * (deg / max_deg), 1),
            "font": {"size": 12 if deg >= max_deg * 0.15 else 0, "color": "#ffffff"},
            "title": label, "module": mod,
            "source_file": sanitize(n.get("source_file", "")), "file_type": n.get("file_type", ""),
            "local_id": sanitize(n.get("local_id", "")), "degree": deg,
        })
    vis_edges = []
    for e in links:
        relation = e.get("relation", "")
        confidence = e.get("confidence", "EXTRACTED")
        vis_edges.append({
            "from": e.get("source", ""), "to": e.get("target", ""),
            "label": relation, "title": sanitize(f"{relation} [{confidence}]"),
            "dashes": confidence != "EXTRACTED",
            "width": 2 if confidence == "EXTRACTED" else 1,
            "color": {"opacity": 0.7 if confidence == "EXTRACTED" else 0.35},
        })
    return vis_nodes, vis_edges

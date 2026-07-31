#!/usr/bin/env python3
"""Generate a module-grouped graph.html from graphify-out/graph.json.

Groups communities under per-app/module section headers in the sidebar legend
and colors nodes by module (base hue per module, shade per community) so the
graph is visually organized by app while keeping every edge intact.

Usage:
    python scripts/graphify-html-grouped.py [--graph PATH] [--out PATH]
"""
import html as _html
import json
import sys
from collections import Counter
from pathlib import Path

DEFAULT_GRAPH = Path("graphify-out/graph.json")
DEFAULT_OUT = Path("graphify-out/graph.html")

MODULE_ORDER = [
    "commonlib", "backend", "web", "scrapper", "aiEnrich", "aiEnrichNew",
    "aiEnrich3", "aiEnrichSkill", "aiCvMatcher", "aiFormFiller", "cron",
]

TPL_PATH = Path(__file__).parent / "templates" / "graphify-html.tpl"

def _js_safe(obj) -> str:
    """Escape </script> sequences so embedded JSON cannot break out of the script tag."""
    return json.dumps(obj).replace("</", "<\\/")

def _sanitize(value) -> str:
    return _html.escape(str(value or ""))

def hsl_to_hex(h: float, s: float, l: float) -> str:
    """Convert HSL (0-360 / 0-1 / 0-1) to a #rrggbb hex string."""
    h = h % 360
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2
    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    return "#{:02x}{:02x}{:02x}".format(
        round((r + m) * 255), round((g + m) * 255), round((b + m) * 255)
    )

def module_order(modules: set[str]) -> list[str]:
    ordered = [m for m in MODULE_ORDER if m in modules]
    ordered.extend(sorted(m for m in modules if m not in MODULE_ORDER))
    return ordered

def community_colors(communities: list[int], base_hue: float) -> dict[int, str]:
    colors: dict[int, str] = {}
    for ci, cid in enumerate(communities):
        lightness = 0.40 + 0.08 * (ci % 5)
        colors[cid] = hsl_to_hex(base_hue + (ci * 7) % 20 - 10, 0.55, lightness)
    return colors

def generate_html(graph_path: Path, out_path: Path) -> None:
    data = json.loads(graph_path.read_text(encoding="utf-8"))
    if "links" not in data and "edges" in data:
        data = dict(data, links=data["edges"])
    nodes = data.get("nodes", [])
    links = data.get("links", [])

    degree = Counter()
    for e in links:
        degree[e.get("source", "")] += 1
        degree[e.get("target", "")] += 1

    communities: dict[int, list[dict]] = {}
    for n in nodes:
        cid = n.get("community")
        if cid is not None:
            communities.setdefault(cid, []).append(n)

    community_module: dict[int, str] = {}
    community_name: dict[int, str] = {}
    for cid, members in communities.items():
        repos = Counter(n.get("repo", "unknown") for n in members)
        community_module[cid] = repos.most_common(1)[0][0]
        community_name[cid] = next((n.get("community_name") for n in members if n.get("community_name")), None) or f"Community {cid}"

    modules = module_order(set(community_module.values()))
    base_hues = {m: i * 360.0 / len(modules) for i, m in enumerate(modules)}
    module_hex = {m: hsl_to_hex(h, 0.55, 0.52) for m, h in base_hues.items()}
    community_color: dict[int, str] = {}
    for m in modules:
        m_cids = sorted(
            (cid for cid, mod in community_module.items() if mod == m),
            key=lambda cid: -len(communities[cid]),
        )
        community_color.update(community_colors(m_cids, base_hues[m]))

    node_module: dict[str, str] = {}
    for n in nodes:
        node_module[n["id"]] = n.get("repo", community_module.get(n.get("community"), "unknown"))

    max_deg = max(degree.values(), default=1) or 1
    vis_nodes = []
    for n in nodes:
        nid = n["id"]
        color = community_color.get(n.get("community"), module_hex.get(node_module.get(nid, ""), "#4E79A7"))
        label = _sanitize(n.get("label", nid))
        deg = degree.get(nid, 1)
        size = 10 + 30 * (deg / max_deg)
        font_size = 12 if deg >= max_deg * 0.15 else 0
        vis_nodes.append({
            "id": nid,
            "label": label,
            "color": {"background": color, "border": color, "highlight": {"background": "#ffffff", "border": color}},
            "size": round(size, 1),
            "font": {"size": font_size, "color": "#ffffff"},
            "title": _sanitize(label),
            "community": n.get("community"),
            "community_name": _sanitize(n.get("community_name", f"Community {n.get('community')}")),
            "module": node_module.get(nid, ""),
            "source_file": _sanitize(n.get("source_file", "")),
            "file_type": n.get("file_type", ""),
            "degree": deg,
        })

    vis_edges = []
    for e in links:
        confidence = e.get("confidence", "EXTRACTED")
        relation = e.get("relation", "")
        vis_edges.append({
            "from": e.get("source", ""),
            "to": e.get("target", ""),
            "label": relation,
            "title": _sanitize(f"{relation} [{confidence}]"),
            "dashes": confidence != "EXTRACTED",
            "width": 2 if confidence == "EXTRACTED" else 1,
            "color": {"opacity": 0.7 if confidence == "EXTRACTED" else 0.35},
            "confidence": confidence,
        })

    module_data = []
    for m in modules:
        m_cids = [cid for cid, mod in community_module.items() if mod == m]
        module_data.append({
            "module": m,
            "color": module_hex[m],
            "count": sum(len(communities[cid]) for cid in m_cids),
            "communities": [
                {
                    "cid": cid,
                    "label": _sanitize(community_name[cid]),
                    "count": len(communities[cid]),
                    "color": community_color[cid],
                }
                for cid in sorted(m_cids, key=lambda cid: -len(communities[cid]))
            ],
        })

    total_communities = len(communities)
    title = _sanitize(str(out_path))
    stats = f"{len(nodes)} nodes &middot; {len(links)} edges &middot; {total_communities} communities &middot; {len(modules)} modules"
    html = (TPL_PATH.read_text(encoding="utf-8")
        .replace("__TITLE__", title)
        .replace("__STATS__", stats)
        .replace("__NODES_JSON__", _js_safe(vis_nodes))
        .replace("__EDGES_JSON__", _js_safe(vis_edges))
        .replace("__MODULES_JSON__", _js_safe(module_data))
        .replace("__TOTAL_COMMUNITIES__", str(total_communities)))
    out_path.write_text(html, encoding="utf-8")
    print(f"Wrote {out_path} ({len(nodes)} nodes, {len(links)} edges, {total_communities} communities, {len(modules)} modules)")

def main():
    graph_path = DEFAULT_GRAPH
    out_path = DEFAULT_OUT
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--graph" and i + 1 < len(args):
            graph_path = Path(args[i + 1])
            i += 2
        elif args[i] == "--out" and i + 1 < len(args):
            out_path = Path(args[i + 1])
            i += 2
        else:
            i += 1
    if not graph_path.exists():
        print(f"ERROR: graph not found: {graph_path}", file=sys.stderr)
        sys.exit(1)
    generate_html(graph_path, out_path)

if __name__ == "__main__":
    main()

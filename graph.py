# Graph store — embedded, single JSON file. No native dependency, no server.
# A "graph" here is a node map (entities + personas) and an edge list (relationships).
# JSON is more than enough for 5–16 nodes and makes run history trivially inspectable.

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple


class GraphStore:
    """One file, two dicts: nodes {key: node-dict}, edges [(src, dst, label)].

    `clear()` resets the store. The engine calls it at the start of every run so a
    fresh simulation doesn't inherit stale nodes from previous runs (the per-run
    graph is what's persisted in the run folder — this store is only the live view)."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.nodes: Dict[str, dict] = {}
        self.edges: List[Tuple[str, str, str]] = []
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
                self.nodes = data.get("nodes", {})
                self.edges = [tuple(e) for e in data.get("edges", [])]
            except Exception:
                self.nodes, self.edges = {}, []

    def clear(self) -> None:
        self.nodes, self.edges = {}, []
        self.save()

    # ── writes ────────────────────────────────────────────────────────
    def add_node(self, key: str, **attrs) -> None:
        self.nodes[key] = attrs

    def add_edge(self, src: str, dst: str, label: str) -> None:
        if not any(s == src and d == dst for s, d, _ in self.edges):
            self.edges.append((src, dst, label))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"nodes": self.nodes, "edges": self.edges}, indent=1)
        )

    # ── reads ─────────────────────────────────────────────────────────
    def nodes_of_kind(self, kind: str) -> List[dict]:
        return [n for n in self.nodes.values() if n.get("kind") == kind]

    def neighbors(self, key: str) -> List[str]:
        return [d for s, d, _ in self.edges if s == key] + [
            s for s, d, _ in self.edges if d == key
        ]

    def as_payload(self, camps: List[dict] | None = None) -> Dict[str, object]:
        """Shape the desktop SVG renderer consumes. `camps` (optional) tags each
        node with its camp name so the UI can cluster-color or label."""
        camp_of = {}
        if camps:
            for c in camps:
                for m in c.get("members", []):
                    camp_of[m] = c.get("name", "?")
        nodes = [
            {"id": k, "name": v.get("name", k), "kind": v.get("kind", ""),
             "stance": v.get("stance", 0.0), "camp": camp_of.get(v.get("name", k), "")}
            for k, v in self.nodes.items()
        ]
        edges = [
            {"from": s, "to": d, "label": lbl} for s, d, lbl in self.edges
        ]
        return {"nodes": nodes, "edges": edges, "camps": camps or []}

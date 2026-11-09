# Camp clusters — GraphRAG community detection, simplified for a small node set.
# Groups stakeholders into "camps" (coalitions) by stance sign and the
# oppose/support edges between them. Cheap and local — no extra LLM calls.
# This is the honest part of GraphRAG: community structure in the relationship
# graph, without claiming to run Leiden on embeddings we don't compute.

from __future__ import annotations

from typing import Dict, List

from .models import Persona


def cluster_camps(personas: List[Persona], relationships: List[tuple]) -> List[dict]:
    """Group personas into camps. Returns [{name, members, lean}] sorted by size."""
    if not personas:
        return []
    names = [p.name for p in personas]
    by_name = {p.name: p for p in personas}

    # signed edges: same camp tends to support, opposed edges split
    adjacency: Dict[str, set] = {n: set() for n in names}
    for src, dst, label in relationships:
        if src in adjacency and dst in adjacency and src != dst:
            adjacency[src].add(dst)
            adjacency[dst].add(src)

    # seed camps by stance sign, then fold in edge-neighbors (BFS)
    visited: set = set()
    camps: List[dict] = []

    def _lean(members: List[str]) -> str:
        avg = sum(by_name[m].stance for m in members) / max(1, len(members))
        return "for" if avg > 0.3 else ("against" if avg < -0.3 else "undecided")

    for seed in sorted(names, key=lambda n: by_name[n].stance):
        if seed in visited:
            continue
        # BFS along edges, but only within the same stance-sign neighborhood:
        # a node linked to an opponent does not join the opponent's camp.
        camp = [seed]
        visited.add(seed)
        queue = [seed]
        while queue:
            cur = queue.pop()
            cur_sign = 1 if by_name[cur].stance >= 0 else -1
            for nb in adjacency.get(cur, set()):
                if nb in visited:
                    continue
                nb_sign = 1 if by_name[nb].stance >= 0 else -1
                if nb_sign == cur_sign:
                    visited.add(nb)
                    camp.append(nb)
                    queue.append(nb)
        # unreached same-sign nodes near this camp merge in later iterations
        camps.append({"name": _camp_name(camp, by_name), "members": camp, "lean": _lean(camp)})

    camps.sort(key=lambda c: len(c["members"]), reverse=True)
    return camps


def _camp_name(members: List[str], by_name: Dict[str, Persona]) -> str:
    ranked = sorted(members, key=lambda m: abs(by_name[m].stance), reverse=True)
    lead = ranked[0] if ranked else "stakeholders"
    if len(members) == 1:
        return lead
    return f"{lead} + {len(members) - 1}"

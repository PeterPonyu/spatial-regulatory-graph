from __future__ import annotations
from .contracts import RegulatoryEdge


def normalize_external_edge_rows(rows: list[dict[str, object]]) -> tuple[RegulatoryEdge, ...]:
    edges = []
    for row in rows:
        edges.append(RegulatoryEdge(str(row["regulator"]), str(row["target"]), "coexpression_candidate", float(row.get("score", 0.0)), "unknown", evidence_used=("expression",), uncertainty=None))
    return tuple(edges)

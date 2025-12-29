from typing import Dict, Any, List, Tuple
import math
from .memory import MemorySystem


def build_memory_graph(memory: MemorySystem) -> Dict[str, List[Dict[str, Any]]]:
    """
    Returns a basic graph representation:
    - nodes: memories
    - edges: explicit links
    """
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    for i, m in enumerate(memory.memories):
        nodes.append(
            {
                "id": i,
                "label": f"{i}:{m.kind}",
                "kind": m.kind,
                "emotion_valence": m.emotion_valence,
            }
        )
        for target in m.links:
            edges.append({"source": i, "target": target})

    return {"nodes": nodes, "edges": edges}


def layout_memory_graph(
    nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Simple radial layout:
    - nodes positioned on a circle by index
    """
    n = max(1, len(nodes))
    radius = 1.0

    for idx, node in enumerate(nodes):
        angle = 2 * math.pi * idx / n
        node["x"] = radius * math.cos(angle)
        node["y"] = radius * math.sin(angle)

    return nodes, edges


def graph_for_visualisation(memory: MemorySystem, active_path: List[int]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Build graph, compute layout, and mark active nodes/edges.
    """
    graph = build_memory_graph(memory)
    nodes, edges = layout_memory_graph(graph["nodes"], graph["edges"])

    active_set = set(active_path or [])

    # Mark active nodes
    for n in nodes:
        n["active"] = n["id"] in active_set

    # Mark active edges (both ends must be active)
    for e in edges:
        e["active"] = (e["source"] in active_set and e["target"] in active_set)

    return {"nodes": nodes, "edges": edges}

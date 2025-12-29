from typing import Dict, Any, List
from .memory import MemorySystem


def build_memory_graph(memory: MemorySystem) -> Dict[str, List[Dict[str, Any]]]:
    """
    Returns a basic graph representation:
    - nodes: memories
    - edges: explicit links
    """
    nodes = []
    edges = []

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

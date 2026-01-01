from dataclasses import dataclass
from typing import Any, Dict, List, Set, Tuple
from collections import defaultdict


@dataclass
class ReflectionCluster:
    nodes: List[str]
    strength: float
    label: str


class ReflectionEngine:
    """
    Reflection Pattern 1:
    - Non-verbal replay of connected, external events
    - Builds co-occurrence weights
    - Reinforces frequently co-occurring nodes
    - Applies gentle decay to unused, weak nodes
    """
    def __init__(self):
        self.last_clusters: List[ReflectionCluster] = []
        self.last_weights: Dict[Tuple[str, str], float] = {}

    def run_pattern_1(self, day_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Collect nodes per event (external truth only)
        event_nodes: List[Set[str]] = []
        for ev in day_events:
            nodes = set()

            # entities
            for eid in ev.get("entities", []):
                nodes.add(f"ent:{eid}")

            # objects
            for oid in ev.get("objects", []):
                nodes.add(f"obj:{oid}")

            # place
            place = ev.get("place")
            if place:
                nodes.add(f"place:{place}")

            # sensory
            for s in ev.get("smells", []):
                nodes.add(f"smell:{s}")
            for s in ev.get("sounds", []):
                nodes.add(f"sound:{s}")

            # emotion tag (external builder can provide)
            emo = ev.get("emotion")
            if emo:
                nodes.add(f"emo:{emo}")

            if nodes:
                event_nodes.append(nodes)

        # Build co-occurrence weights
        weights = defaultdict(float)
        node_freq = defaultdict(float)

        for nodes in event_nodes:
            nodes_list = list(nodes)
            for n in nodes_list:
                node_freq[n] += 1.0
            for i in range(len(nodes_list)):
                for j in range(i + 1, len(nodes_list)):
                    a, b = nodes_list[i], nodes_list[j]
                    if a > b:
                        a, b = b, a
                    weights[(a, b)] += 1.0

        self.last_weights = dict(weights)

        # Build simple clusters: strongest pairs expanded by shared nodes
        clusters: List[ReflectionCluster] = []
        # Sort edges by weight descending
        edges_sorted = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)

        used_nodes = set()
        for (a, b), w in edges_sorted[:12]:  # cap to keep fast
            # Build cluster seed
            cluster_nodes = {a, b}

            # expand: add nodes that co-occur strongly with either a or b
            for (x, y), w2 in weights.items():
                if w2 < 2:
                    continue
                if x in cluster_nodes or y in cluster_nodes:
                    cluster_nodes.add(x)
                    cluster_nodes.add(y)

            # compute strength
            strength = sum(node_freq[n] for n in cluster_nodes) / max(1.0, len(cluster_nodes))
            label = " ↔ ".join(sorted(list(cluster_nodes))[:4])
            clusters.append(ReflectionCluster(nodes=sorted(list(cluster_nodes)), strength=float(strength), label=label))

            used_nodes |= cluster_nodes
            if len(clusters) >= 6:
                break

        # Fallback cluster: most frequent nodes
        if not clusters and node_freq:
            top = sorted(node_freq.items(), key=lambda kv: kv[1], reverse=True)[:8]
            clusters.append(ReflectionCluster(nodes=[k for k, _ in top], strength=float(top[0][1]), label="Top nodes"))

        self.last_clusters = clusters

        return {
            "clusters": [c.__dict__ for c in clusters],
            "node_freq": dict(node_freq),
            "edge_count": len(weights),
            "event_count": len(event_nodes),
        }

    def reinforce_entities(self, bridge_entities: Dict[str, Any], node_freq: Dict[str, float]) -> Dict[str, Any]:
        """
        Increase confidence only for entities that appeared in external replay.
        Apply small decay for entities not replayed (prevents clutter).
        """
        reinforced = []
        decayed = []

        # determine which ent IDs were present
        present_ent_ids = set()
        for node in node_freq.keys():
            if node.startswith("ent:"):
                present_ent_ids.add(node.split("ent:", 1)[1])

        # reinforce present
        for eid in present_ent_ids:
            e = bridge_entities.get(eid)
            if not e:
                continue
            old = float(getattr(e, "confidence", 1.0))
            new = min(1.0, old + 0.02)
            setattr(e, "confidence", new)
            if new != old:
                reinforced.append((getattr(e, "name", eid), old, new))

        # decay absent (gentle)
        for eid, e in bridge_entities.items():
            if eid in present_ent_ids:
                continue
            old = float(getattr(e, "confidence", 1.0))
            # don't decay the agent or locked speaker too aggressively
            if getattr(e, "kind", "") == "agent":
                continue
            if old <= 0.35:
                continue
            new = max(0.30, old - 0.01)
            setattr(e, "confidence", new)
            if new != old:
                decayed.append((getattr(e, "name", eid), old, new))

        return {"reinforced": reinforced, "decayed": decayed}
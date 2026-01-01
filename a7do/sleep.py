from collections import defaultdict
from typing import Dict, Any

class SleepEngine:
    """
    Replay only, plus observer-facing cluster stats.
    No new facts invented.
    """

    def replay(self, experiences) -> Dict[str, Any]:
        recent = experiences.recent(8)
        edge = defaultdict(int)

        # co-presence edges (place-agent-object)
        for ev in recent:
            a = f"agent:{ev.agent}"
            r = f"room:{ev.room}"
            edge[(a, r)] += 1
            if ev.obj:
                o = f"obj:{ev.obj}"
                edge[(o, r)] += 1
                edge[(a, o)] += 1
            if ev.to_room:
                tr = f"room:{ev.to_room}"
                edge[(r, tr)] += 1

        # build top edges for observer
        top_edges = sorted(edge.items(), key=lambda x: x[1], reverse=True)[:12]
        readable = [{"a": k[0], "b": k[1], "w": v} for k, v in top_edges]

        return {
            "replayed_count": len(recent),
            "top_edges": readable,
            "note": "Replay + reinforcement stats only (no abstraction)."
        }
import time
from collections import defaultdict
from typing import Dict, List, Tuple


class ReoccurrenceTracker:
    """
    Tracks what keeps showing up together across events.
    This is the 'reinforcement without overload' layer.
    """

    def __init__(self):
        self.entity_pair_counts = defaultdict(int)    # (a,b) -> count
        self.entity_env_counts = defaultdict(int)     # (entity, env) -> count
        self.entity_emotion_counts = defaultdict(int) # (entity, emotion) -> count
        self.last_seen = {}                           # key -> timestamp

    def _canon_pair(self, a: str, b: str) -> Tuple[str, str]:
        return (a, b) if a <= b else (b, a)

    def ingest_event(self, event_entities: List[str], env: Dict[str, float], emo: Dict[str, float]):
        now = time.time()

        # entity-entity co-occurrence
        for i in range(len(event_entities)):
            for j in range(i + 1, len(event_entities)):
                pair = self._canon_pair(event_entities[i], event_entities[j])
                self.entity_pair_counts[pair] += 1
                self.last_seen[("pair", pair)] = now

        # entity-environment
        for e in event_entities:
            for k in env.keys():
                self.entity_env_counts[(e, k)] += 1
                self.last_seen[("env", e, k)] = now

        # entity-emotion
        for e in event_entities:
            for k in emo.keys():
                self.entity_emotion_counts[(e, k)] += 1
                self.last_seen[("emo", e, k)] = now

    def top_pairs(self, n=10):
        return sorted(self.entity_pair_counts.items(), key=lambda x: x[1], reverse=True)[:n]

    def summary(self):
        return {
            "top_entity_pairs": [({"a": a, "b": b}, c) for (a, b), c in self.top_pairs(10)],
            "pair_count": len(self.entity_pair_counts),
            "entity_env_count": len(self.entity_env_counts),
            "entity_emotion_count": len(self.entity_emotion_counts),
        }
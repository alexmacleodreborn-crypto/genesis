import time
from collections import defaultdict


class EntityFactLedger:
    """
    Tracks candidate facts and aliases for entities
    and promotes them using confidence rules.
    """

    def __init__(self):
        # entity_id -> fact_key -> data
        self.candidates = defaultdict(dict)
        self.facts = defaultdict(dict)
        self.aliases = defaultdict(set)

    # --------------------------------------------------

    def add_candidate(self, entity_id: str, key: str, source: str):
        now = time.time()

        c = self.candidates[entity_id].setdefault(key, {
            "count": 0,
            "sources": set(),
            "first_seen": now,
            "last_seen": now
        })

        c["count"] += 1
        c["sources"].add(source)
        c["last_seen"] = now

    # --------------------------------------------------
    # Promotion rules
    # --------------------------------------------------

    def try_promote_identity(self, entity_id: str, key: str):
        """
        Identity facts require:
        - repetition
        - time separation
        - childhood + adult sources
        """
        c = self.candidates[entity_id].get(key)
        if not c:
            return False

        if c["count"] < 3:
            return False

        if len(c["sources"]) < 2:
            return False

        if (c["last_seen"] - c["first_seen"]) < 5:
            return False

        self.facts[entity_id][key] = c
        del self.candidates[entity_id][key]
        return True

    def try_promote_alias(self, entity_id: str, alias: str):
        """
        Aliases require:
        - repetition
        - time separation
        """
        c = self.candidates[entity_id].get(f"alias:{alias}")
        if not c:
            return False

        if c["count"] < 2:
            return False

        if (c["last_seen"] - c["first_seen"]) < 5:
            return False

        self.aliases[entity_id].add(alias)
        del self.candidates[entity_id][f"alias:{alias}"]
        return True

    # --------------------------------------------------

    def summary(self):
        return {
            "candidates": {
                eid: dict(v) for eid, v in self.candidates.items()
            },
            "facts": {
                eid: dict(v) for eid, v in self.facts.items()
            },
            "aliases": {
                eid: list(v) for eid, v in self.aliases.items()
            }
        }
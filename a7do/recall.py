from typing import List, Optional
from a7do.event_graph import Event


class RecallEngine:
    """
    Recall v1: grounded episodic recall
    - event-based
    - factual
    - no inference or imagination
    """

    def __init__(self, event_graph, entities):
        self.event_graph = event_graph
        self.entities = entities

    def recall(
        self,
        *,
        entity_name: Optional[str] = None,
        place: Optional[str] = None,
        limit: int = 5,
    ) -> List[Event]:

        events = list(self.event_graph.events.values())

        def matches(ev: Event) -> bool:
            if entity_name:
                for eid in ev.participants:
                    ent = self.entities.get(eid)
                    if ent and ent.name.lower() == entity_name.lower():
                        return True
                return False

            if place:
                return ev.place == place

            return False

        matched = [ev for ev in events if matches(ev)]
        matched.sort(key=lambda e: e.timestamp, reverse=True)
        return matched[:limit]

    def format(self, events: List[Event]) -> str:
        if not events:
            return "I don’t remember anything about that yet."

        lines = []
        for ev in events:
            parts = []

            if ev.place:
                parts.append(f"at the {ev.place}")

            names = []
            for eid in ev.participants:
                ent = self.entities.get(eid)
                if ent:
                    names.append(ent.name)
            if names:
                parts.append("with " + ", ".join(names))

            sentence = "I remember being " + " ".join(parts) + "."

            if ev.smells:
                smells = ", ".join(s.replace("_smell", "") for s in ev.smells)
                sentence += f" It smelled like {smells}."

            if ev.sounds:
                sounds = ", ".join(s.replace("_sound", "") for s in ev.sounds)
                sentence += f" I could hear {sounds}."

            lines.append(sentence)

        return " ".join(lines)
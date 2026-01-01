class RecallEngine:
    def __init__(self, events, entities):
        self.events = events
        self.entities = entities

    def recall(self, entity_name=None, place=None):
        results = []
        for ev in self.events.events:
            if place and ev.place == place:
                results.append(ev)
            if entity_name:
                for pid in ev.participants:
                    if self.entities[pid].name.lower() == entity_name.lower():
                        results.append(ev)
        return results

    def format(self, events):
        if not events:
            return "I don't remember anything."
        return "\n".join(e.description for e in events)
class ExperienceEvent:
    """
    A single situated experience.
    """

    def __init__(
        self,
        place: str,
        agent: str,
        action: str,
        obj: str = None,
        emphasis=None,
        environment=None
    ):
        self.place = place
        self.agent = agent
        self.action = action
        self.object = obj
        self.emphasis = emphasis or []
        self.environment = environment or {}

    def to_phrase(self):
        parts = [self.agent, self.action]
        if self.object:
            parts.append(self.object)
        return " ".join(parts)


class ExperienceStore:
    def __init__(self):
        self.events = []

    def add(self, event: ExperienceEvent):
        self.events.append(event)

    def recent(self, n=5):
        return self.events[-n:]
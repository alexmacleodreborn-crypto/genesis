class Schedule:
    """
    Always-present schedule with place context.
    """

    def __init__(self):
        self.day = 0
        self.place = "home"
        self.events = []
        self.state = "waiting"

    def load_day(self, day, place, events):
        self.day = day
        self.place = place
        self.events = events
        self.state = "waiting"

    def wake(self):
        self.state = "awake"

    def next_event(self):
        if self.events:
            return self.events.pop(0)
        return None

    def sleep(self):
        self.state = "asleep"

    def complete(self):
        self.state = "complete"
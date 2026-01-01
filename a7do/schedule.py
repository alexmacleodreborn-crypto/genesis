class DaySchedule:
    """
    Infant day:
    wait → wake → learn → sleep
    """

    def __init__(self):
        self.started = False
        self.completed = False

    def start(self):
        self.started = True
        self.completed = False

    def end(self):
        self.completed = True
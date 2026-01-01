from a7do.experience import ExperienceStore
from a7do.lexicon import Lexicon
from a7do.sleep import SleepEngine


class A7DOMind:
    """
    Infant cognition — situated learning only.
    """

    def __init__(self, schedule):
        self.schedule = schedule
        self.experiences = ExperienceStore()
        self.lexicon = Lexicon()
        self.sleep_engine = SleepEngine()
        self.last = None

    def wake(self):
        self.last = "wake"

    def process_event(self, event):
        self.experiences.add(event)
        self.lexicon.learn_from_event(event)
        self.last = f"experienced in {event.place}"

    def sleep(self):
        self.last = "sleep"
        return self.sleep_engine.replay(self.experiences)
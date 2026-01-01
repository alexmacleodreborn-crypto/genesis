from a7do.experience import ExperienceStore
from a7do.lexicon import Lexicon
from a7do.sleep import SleepEngine


class A7DOMind:
    """
    Infant cognition.
    """

    def __init__(self, schedule):
        self.schedule = schedule
        self.experiences = ExperienceStore()
        self.lexicon = Lexicon()
        self.sleep_engine = SleepEngine()
        self.last = None

    def wake(self):
        self.last = "wake"

    def process_event(self, text):
        self.experiences.add(text)
        self.lexicon.learn(text)
        self.last = f"experienced: {text}"

    def sleep(self):
        self.last = "sleep"
        return self.sleep_engine.replay(self.experiences)
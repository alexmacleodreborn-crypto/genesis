from a7do.schedule import DaySchedule
from a7do.experience import ExperienceStore
from a7do.lexicon import Lexicon
from a7do.sleep import SleepEngine


class A7DOMind:
    """
    Infant-stage cognitive core.
    No free chat. No inference. No invention.
    """

    def __init__(self):
        self.schedule = DaySchedule()
        self.experiences = ExperienceStore()
        self.lexicon = Lexicon()
        self.sleep_engine = SleepEngine()

        self.awake = False
        self.last_action = None

    # -------------------------
    # Lifecycle
    # -------------------------
    def wake(self):
        self.awake = True
        self.last_action = "wake"

    def sleep(self):
        self.awake = False
        self.last_action = "sleep"
        return self.sleep_engine.replay(self.experiences)

    # -------------------------
    # Learning intake
    # -------------------------
    def process_experience(self, phrase: str):
        """
        Phrase is intentionally simple:
        'this is a dog'
        'look dog'
        'clap dog'
        'red dog'
        """
        if not self.awake:
            return "A7DO is sleeping."

        phrase = phrase.lower().strip()
        tokens = phrase.split()

        self.experiences.add_raw_phrase(phrase)

        # primitive language learning
        self.lexicon.learn_from_tokens(tokens)

        self.last_action = f"learned: {phrase}"
        return f"A7DO sees: {phrase}"
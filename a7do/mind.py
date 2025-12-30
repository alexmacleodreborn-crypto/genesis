import time

from a7do.coherence import CoherenceScorer
from a7do.profile import ProfileManager
from a7do.tagger import Tagger
from a7do.background_density import BackgroundDensity
from a7do.language_curriculum import LanguageCurriculum
from a7do.entities import EntityGraph
from .entity_facts import EntityFactLedger


class A7DOMind:
    def __init__(self, identity, emotion, memory, development, multi_agent, childhood):
        self.identity = identity
        self.emotion = emotion
        self.memory = memory
        self.development = development
        self.multi_agent = multi_agent
        self.childhood = childhood

        self.tagger = Tagger()
        self.profiles = ProfileManager()
        self.density = BackgroundDensity()
        self.entities = EntityGraph()
        self.facts = EntityFactLedger()
        self.curriculum = LanguageCurriculum(drip_seconds=10)

        self.unbound_names = {}

        self.events = []
        self.path = []
        self.last_coherence = None

    # --------------------------------------------------

    def emit(self, phase, msg):
        self.events.append(f"[{phase}] {msg}")
        self.path.append(phase)
        time.sleep(0.002)

    # --------------------------------------------------

    def process(self, text: str):
        self.events.clear()
        self.path.clear()

        tags = list(self.tagger.tag(text).keys())

        # Ensure user entity
        user = self.entities.find_by_name_or_alias(self.identity.user_name)
        if not user:
            user = self.entities.create("person")
            user.add_name(self.identity.user_name)

        source = "childhood" if self.childhood.is_simple_input(text) else "adult"
        t = text.lower()

        current_entities = []

        # --------------------------------------------------
        # ENTITY DETECTION (STRUCTURAL)
        # --------------------------------------------------

        if "dog" in t:
            dog = self.entities.create("animal")
            dog.add_attribute("species:dog", 1.0)
            dog.link("owner", user.id)
            user.link("owns", dog.id)
            current_entities.append(dog)

            self.facts.add_candidate(dog.id, "identity:dog", source)
            self.facts.try_promote_identity(dog.id, "identity:dog")
            self.emit("ENTITY", "Dog entity detected")

        # --------------------------------------------------
        # NAME / ALIAS HANDLING
        # --------------------------------------------------

        for word in text.split():
            if not word.istitle():
                continue

            e = self.entities.find_by_name_or_alias(word)
            if e:
                self.facts.add_candidate(e.id, f"alias:{word}", "adult")
                self.facts.try_promote_alias(e.id, word)
                self.emit("ALIAS", f"Alias candidate: {word}")
            else:
                self.unbound_names[word] = {
                    "count": self.unbound_names.get(word, {}).get("count", 0) + 1,
                    "last_seen": time.time(),
                    "source": source
                }
                self.emit("NAME", f"Unbound name: {word}")

        # --------------------------------------------------
        # BIND UNBOUND NAMES
        # --------------------------------------------------

        if current_entities and self.unbound_names:
            for name, info in list(self.unbound_names.items()):
                for e in current_entities:
                    e.add_name(name)
                    self.facts.add_candidate(e.id, f"name:{name}", info["source"])
                    self.facts.try_promote_identity(e.id, f"name:{name}")
                    self.emit("BIND", f"Bound name {name}")
                del self.unbound_names[name]

        # --------------------------------------------------
        # MEMORY
        # --------------------------------------------------

        self.memory.add(kind="utterance", content=text, tags=tags)

        # --------------------------------------------------
        # IDENTITY QUERIES
        # --------------------------------------------------

        if self.identity.is_user_identity_question(text):
            return self._who_am_i(user)

        # --------------------------------------------------
        # RESPONSE LOGIC
        # --------------------------------------------------

        if self.facts.facts:
            answer = "I’m forming a clearer understanding. You can ask who someone is."
        else:
            answer = "I’m learning from this."

        return {
            "answer": answer,
            "events": self.events,
            "path": self.path,
            "entities": self.entities.summary(),
            "facts": self.facts.summary(),
        }

    # --------------------------------------------------

    def _who_am_i(self, user):
        return {
            "answer": f"You are {self.identity.user_name}, the creator of this system.",
            "events": self.events,
            "path": self.path,
            "entities": self.entities.summary(),
            "facts": self.facts.summary(),
        }
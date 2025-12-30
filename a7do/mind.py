import time

from a7do.coherence import CoherenceScorer
from a7do.profile import ProfileManager
from a7do.tagger import Tagger
from a7do.background_density import BackgroundDensity
from a7do.language_curriculum import LanguageCurriculum
from a7do.entities import EntityGraph


class A7DOMind:
    """
    Central cognitive orchestrator for A7DO.
    """

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
        self.curriculum = LanguageCurriculum(drip_seconds=10)

        self.events = []
        self.path = []
        self.last_signals = None
        self.last_coherence = None
        self.last_curriculum_packet = None

        self._coherence = CoherenceScorer()

    # --------------------------------------------------

    def emit(self, phase: str, message: str):
        self.events.append(f"[{phase}] {message}")
        self.path.append(phase)
        time.sleep(0.002)

    # --------------------------------------------------
    # Foundational language drip (always safe)
    # --------------------------------------------------

    def _maybe_drip_language(self):
        if not self.curriculum.ready():
            return

        pkt = self.curriculum.next_packet()
        self.last_curriculum_packet = pkt

        self.memory.add(
            kind="foundational",
            content=f"{pkt['title']}: {pkt['content']}",
            tags=pkt["tags"]
        )

        self.density.ingest(
            f"[FOUNDATIONAL] {pkt['title']}",
            pkt["tags"]
        )

        self.emit("FOUNDATIONAL", f"Language drip: {pkt['title']}")

    # --------------------------------------------------
    # Entity update (structure only — NO FACTS)
    # --------------------------------------------------

    def _update_entities(self, text: str):
        # Ensure user entity exists
        user = self.entities.find_by_name(self.identity.user_name)
        if not user:
            user = self.entities.create("person")
            user.add_name(self.identity.user_name)

        t = text.lower()

        # Extremely conservative animal detection
        if "dog" in t:
            animal = self.entities.create("animal")
            animal.add_attribute("species:dog", 1.0)

            if "rott" in t:
                animal.add_attribute("breed:rottweiler", 1.0)

            if "trained" in t:
                animal.add_role("trained")

            if "support" in t or "adhd" in t or "autism" in t:
                animal.add_role("support_animal")

            animal.link("owner", user.id)
            user.link("owns", animal.id)

    # --------------------------------------------------

    def process(self, text: str) -> dict:
        self.events.clear()
        self.path.clear()

        # 1) Developmental language exposure
        self._maybe_drip_language()

        self.emit("INPUT", "User input received")

        # 2) Tagging
        tags_map = self.tagger.tag(text)
        tags = list(tags_map.keys())
        self.emit("TAGGING", f"Domains: {tags if tags else ['none']}")

        # 3) Childhood learning trigger (SAFE + SIMPLE)
        if self.childhood.is_simple_input(text):
            if not self.childhood.is_active():
                self.childhood.start_burst()
                self.emit("CHILDHOOD", "Childhood learning burst started")

            self.childhood.absorb(text)

        # 4) Entity structuring
        self._update_entities(text)
        self.emit("ENTITIES", "Entity graph updated")

        # 5) Background density ingest
        self.density.ingest(text, tags)
        self.emit("DENSITY", "Background density ingest")

        # 6) Profile learning
        profile = self.profiles.get_or_create(self.identity.user_name)
        profile.learn(text, tags_map)
        self.emit("PROFILE", "Profile updated")

        # 7) Episodic memory
        self.memory.add(kind="utterance", content=text, tags=tags)
        self.emit("MEMORY", "Episodic memory stored")

        # 8) Identity override (explicit only)
        if self.identity.is_user_introduction(text):
            self.identity.capture_user(text)
            self.emit("IDENTITY", "User identity updated")
            return self._result(f"Nice to meet you, {self.identity.user_name}.")

        # 9) User identity query
        if self.identity.is_user_identity_question(text):
            s = profile.summary()
            domains = s.get("domains", {})
            if domains:
                top = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:3]
                answer = "You tend to talk about: " + ", ".join(k for k, _ in top) + "."
            else:
                answer = "I’m still building your profile."
            return self._result(answer)

        # 10) System identity
        if self.identity.is_system_identity_question(text):
            return self._result(self.identity.system_answer())

        # 11) Emotion update
        self.emotion.update(text)
        self.emit("EMOTION", "Emotion updated")

        # 12) Density promotion
        self.density.promote(None)
        self.emit("DENSITY", "Density promoted")

        # 13) Reasoning
        reasoning = self.multi_agent.run(text, mode="deliberation")
        self.last_signals = reasoning.get("signals")

        # 14) Development update
        self.development.update(self.memory)
        self.emit("DEVELOPMENT", "Development updated")

        # 15) Coherence
        if self.last_signals:
            self.last_coherence = self._coherence.score(
                mode="deliberation",
                emotion_value=self.emotion.value,
                signals=self.last_signals
            )

        self.emit("OUTPUT", "Answer ready")
        return self._result(reasoning.get("final", ""))

    # --------------------------------------------------

    def _result(self, answer: str):
        return {
            "answer": answer,
            "events": list(self.events),
            "path": list(self.path),
            "coherence": self.last_coherence,
            "density": self.density.stats(),
            "entities": self.entities.summary(),
            "profiles": self.profiles.summary(),
            "curriculum": self.curriculum.peek_progress(),
            "last_curriculum_packet": self.last_curriculum_packet,
            "childhood": self.childhood.summary(),
        }
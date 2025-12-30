import time
from a7do.coherence import CoherenceScorer
from a7do.profile import ProfileManager
from a7do.tagger import Tagger
from a7do.background_density import BackgroundDensity
from a7do.language_curriculum import LanguageCurriculum


class A7DOMind:
    """
    Central orchestrator with:
    - multi-domain tagging
    - per-person profiling
    - background density buffering
    - confidence learning (candidates/facts)
    - foundational language drip-feed (10s)
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

        self.curriculum = LanguageCurriculum(drip_seconds=10)

        self.events = []
        self.path = []
        self.last_signals = None
        self.last_coherence = None
        self.last_curriculum_packet = None

        self._coherence = CoherenceScorer()

        # promotion policy (if you already added C earlier)
        self.promote_score = 3.0
        self.promote_count = 3

    def emit(self, phase: str, message: str):
        self.events.append(f"[{phase}] {message}")
        self.path.append(phase)
        time.sleep(0.003)

    # -------------------------
    # Foundational drip-feed
    # -------------------------
    def _maybe_drip_language(self):
        """
        Every ~10 seconds, drip one foundational packet into:
        - Memory (kind='foundational')
        - Background density queue (so it stabilises cognition)
        """
        if not self.curriculum.ready():
            return

        pkt = self.curriculum.next_packet()
        self.last_curriculum_packet = pkt

        tags = pkt["tags"]
        title = pkt["title"]
        content = pkt["content"]

        # store as foundational memory (non-personal)
        self.memory.add(
            kind="foundational",
            content=f"{title}: {content}",
            tags=tags
        )

        # also feed background density lightly (as a context stabiliser)
        self.density.ingest(f"[FOUNDATIONAL] {title}", tags)

        self.emit("FOUNDATIONAL", f"Language drip: {title}")

    # -------------------------

    def process(self, text: str) -> dict:
        self.events.clear()
        self.path.clear()

        # 1) Foundational drip runs regardless of user input (progress by exposure)
        self._maybe_drip_language()

        self.emit("INPUT", "User input received")

        # -------------------------
        # Tagging
        # -------------------------
        tags_map = self.tagger.tag(text)
        tags = list(tags_map.keys())
        self.emit("TAGGING", f"Domains: {tags if tags else ['none']}")

        # -------------------------
        # Background density ingest
        # -------------------------
        self.density.ingest(text, tags)
        self.emit("DENSITY", f"Ingested packet (queue={self.density.stats()['queue_len']})")

        # -------------------------
        # Profile learning
        # -------------------------
        profile = self.profiles.get_or_create(self.identity.user_name)
        profile.learn(text, tags_map)
        self.emit("PROFILE", "Language profile updated")

        # -------------------------
        # Episodic memory
        # -------------------------
        self.memory.add(kind="utterance", content=text, tags=tags)
        self.emit("MEMORY", "Tagged memory stored")

        # -------------------------
        # Identity capture (explicit override)
        # -------------------------
        if self.identity.is_user_introduction(text):
            self.emit("IDENTITY", "User identity detected")
            self.identity.capture_user(text)
            self.memory.add(kind="identity", content=f"User is {self.identity.user_name}", tags=["people", "relationship"])
            self.emit("OUTPUT", "Identity stored")
            return self._result(f"Nice to meet you, {self.identity.user_name}.", None, "recognition", "speak")

        # -------------------------
        # User identity query (uses profile + facts if you’ve implemented C)
        # -------------------------
        if self.identity.is_user_identity_question(text):
            self.emit("IDENTITY", "User self-identity query")
            s = profile.summary()
            domains = s.get("domains", {})
            if domains:
                top = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:5]
                answer = "You tend to talk most about: " + ", ".join([k for k, _ in top]) + "."
            else:
                answer = "I’m still building your profile—tell me a few interests or projects you care about."
            self.emit("OUTPUT", "Profile recalled")
            return self._result(answer, None, "recognition", "speak")

        # -------------------------
        # System identity
        # -------------------------
        if self.identity.is_system_identity_question(text):
            self.emit("IDENTITY", "System identity recognised")
            reasoning = self.multi_agent.run(text, mode="recognition")
            self.last_signals = reasoning.get("signals")
            self.emit("OUTPUT", "Identity answer ready")
            return self._result(self.identity.system_answer(), self.last_signals, "recognition", "speak")

        # -------------------------
        # Emotion update
        # -------------------------
        self.emit("EMOTION", "Updating emotional state")
        self.emotion.update(text)

        # -------------------------
        # Promote density to working set
        # -------------------------
        coh_hint = self.last_coherence["score"] if self.last_coherence else None
        self.density.promote(coh_hint)
        self.emit("DENSITY", f"Promoted (working={self.density.stats()['working_len']}, queue={self.density.stats()['queue_len']})")

        working_context = self.density.get_working_context()
        if working_context:
            self.emit("CONTEXT", "Working context prepared")

        # -------------------------
        # Reasoning
        # -------------------------
        self.emit("THINKING", "Deliberative reasoning")
        reasoning = self.multi_agent.run(
            text + ("\n\nWorking context:\n" + working_context if working_context else ""),
            mode="deliberation",
            coherence_hint=coh_hint
        )
        self.last_signals = reasoning.get("signals")

        # -------------------------
        # Development update
        # -------------------------
        self.emit("DEVELOPMENT", "Updating development stage")
        self.development.update(self.memory)

        # -------------------------
        # Coherence scoring
        # -------------------------
        if self.last_signals:
            self.last_coherence = self._coherence.score(
                mode="deliberation",
                emotion_value=self.emotion.value,
                signals=self.last_signals
            )

        self.emit("OUTPUT", "Answer ready")
        return self._result(reasoning.get("final", ""), self.last_signals, "deliberation", "speak")

    # -------------------------

    def _result(self, answer, signals, mode: str, speech_action: str):
        return {
            "answer": answer,
            "events": list(self.events),
            "path": list(self.path),
            "signals": signals,
            "mode": mode,
            "coherence": self.last_coherence,
            "speech_action": speech_action,
            "density": self.density.stats(),
            "profiles": self.profiles.summary(),
            "curriculum_progress": self.curriculum.peek_progress(),
            "last_curriculum_packet": self.last_curriculum_packet,
        }
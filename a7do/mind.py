import time
from a7do.coherence import CoherenceScorer
from a7do.profile import ProfileManager
from a7do.tagger import Tagger
from a7do.background_density import BackgroundDensity


class A7DOMind:
    """
    Central cognitive orchestrator with:
    - multi-domain tagging
    - per-person profiling
    - background density buffering
    - confidence-based memory promotion
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

        self.events = []
        self.path = []
        self.last_signals = None
        self.last_coherence = None

        self._coherence = CoherenceScorer()

        # promotion policy (tune later)
        self.promote_score = 3.0
        self.promote_count = 3

    # --------------------------------------------------

    def emit(self, phase: str, message: str):
        self.events.append(f"[{phase}] {message}")
        self.path.append(phase)
        time.sleep(0.005)

    # --------------------------------------------------

    def process(self, text: str) -> dict:
        self.events.clear()
        self.path.clear()

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
        # Confidence candidates (soft beliefs)
        # -------------------------
        self._update_candidates(text, tags_map)
        self.memory.promote_candidates(
            threshold_score=self.promote_score,
            threshold_count=self.promote_count
        )
        self.emit("PROMOTION", "Candidates updated / promotion checked")

        # -------------------------
        # Childhood learning (optional)
        # -------------------------
        if self.development.STAGES[self.development.index] in ["Birth", "Learning"]:
            if not self.childhood.active:
                self.childhood.start_burst()
                self.emit("CHILDHOOD", "Learning burst started")
            self.childhood.absorb(text)
            if not self.childhood.is_active():
                self.emit("CHILDHOOD", "Learning burst ended")

        # -------------------------
        # Identity capture
        # -------------------------
        if self.identity.is_user_introduction(text):
            self.emit("IDENTITY", "User identity detected")
            self.identity.capture_user(text)
            self.memory.add(kind="identity", content=f"User is {self.identity.user_name}", tags=["people", "relationship"])
            self.emit("OUTPUT", "Identity stored")
            return self._result(f"Nice to meet you, {self.identity.user_name}.", None, "recognition", "speak")

        # -------------------------
        # User profile query
        # -------------------------
        if self.identity.is_user_identity_question(text):
            self.emit("IDENTITY", "User self-identity query")
            answer = self._who_am_i(profile)
            self.emit("OUTPUT", "Profile recalled")
            return self._result(answer, None, "recognition", "speak")

        # -------------------------
        # System identity
        # -------------------------
        if self.identity.is_system_identity_question(text):
            self.emit("IDENTITY", "System identity recognised")
            reasoning = self.multi_agent.run(text, mode="recognition")
            self.last_signals = reasoning["signals"]
            self.last_coherence = self._coherence.score(mode="recognition", emotion_value=self.emotion.value, signals=self.last_signals)
            self.emit("OUTPUT", "Identity answer ready")
            return self._result(self.identity.system_answer(), self.last_signals, "recognition", "speak")

        # -------------------------
        # Emotion update
        # -------------------------
        self.emit("EMOTION", "Updating emotional state")
        self.emotion.update(text)

        # -------------------------
        # Promote density to working context
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
        self.last_signals = reasoning["signals"]

        # -------------------------
        # Development update
        # -------------------------
        self.emit("DEVELOPMENT", "Updating development stage")
        self.development.update(self.memory)

        # -------------------------
        # Coherence scoring
        # -------------------------
        self.last_coherence = self._coherence.score(
            mode="deliberation",
            emotion_value=self.emotion.value,
            signals=self.last_signals
        )

        # -------------------------
        # Speech gate
        # -------------------------
        label = self.last_coherence["label"]
        if label == "RED":
            self.emit("GATE", "Speech blocked (low coherence)")
            answer = "Too much uncertainty right now. Give me one concrete detail or one-sentence goal."
            self.emit("OUTPUT", "Stabiliser response ready")
            return self._result(answer, self.last_signals, "deliberation", "block")

        if label == "AMBER":
            self.emit("GATE", "Cautious speech")
            answer = reasoning["final"] + "\n\n(If you want a tighter answer, give a single goal or example.)"
            self.emit("OUTPUT", "Cautious answer ready")
            return self._result(answer, self.last_signals, "deliberation", "cautious")

        self.emit("GATE", "Speech allowed")
        self.emit("OUTPUT", "Answer ready")
        return self._result(reasoning["final"], self.last_signals, "deliberation", "speak")

    # --------------------------------------------------
    # Candidate update logic
    # --------------------------------------------------

    def _update_candidates(self, text: str, tags_map: dict):
        """
        Convert tags into candidate beliefs with weights.
        This is deliberately conservative.
        """
        # A) Domain interest candidates
        for domain, count in tags_map.items():
            # weight: small per mention, accumulates
            w = 0.6 * count
            self.memory.add_candidate(
                key=f"interest:{domain}",
                weight=w,
                example=text
            )

        # B) Self-reference candidate (helps identity modelling)
        if "relationship" in tags_map:
            self.memory.add_candidate("trait:self_referential", 0.5, text)

        # C) Emotion expression candidate (not the emotion itself, just that it’s present)
        if "emotion" in tags_map:
            self.memory.add_candidate("trait:emotion_expressive", 0.4, text)

    # --------------------------------------------------

    def _who_am_i(self, profile) -> str:
        """
        Evidence-based identity recall: uses promoted facts first, then profile stats.
        """
        facts = self.memory.facts

        top_interests = [k.replace("interest:", "") for k in facts.keys() if k.startswith("interest:")]
        top_interests = top_interests[:5]

        parts = []
        if top_interests:
            parts.append("I can say with confidence you often engage with: " + ", ".join(top_interests) + ".")

        s = profile.summary()
        domains = s.get("domains", {})
        if domains and not top_interests:
            top = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:3]
            parts.append("So far you tend to talk most about: " + ", ".join([k for k, _ in top]) + ".")

        if "trait:self_referential" in facts:
            parts.append("You consistently speak in a first-person way, which helps me model your identity over time.")

        return " ".join(parts) if parts else "I’m still building your profile. Tell me a few interests or projects you care about."

    # --------------------------------------------------

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
            "candidates": self.memory.candidates,
            "facts": self.memory.facts,
        }
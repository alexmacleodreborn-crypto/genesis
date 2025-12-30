import time
from a7do.coherence import CoherenceScorer
from a7do.profile import ProfileManager

class A7DOMind:
    """
    Central cognitive orchestrator.
    Coherence feeds back into thinking.
    """

    def __init__(self, identity, emotion, memory, development, multi_agent, childhood):
        self.identity = identity
        self.emotion = emotion
        self.memory = memory
        self.development = development
        self.multi_agent = multi_agent
        self.childhood = childhood

        self.events = []
        self.path = []
        self.last_signals = None
        self.last_coherence = None

        self._coherence = CoherenceScorer()

    def emit(self, phase: str, message: str):
        self.events.append(f"[{phase}] {message}")
        self.path.append(phase)
        time.sleep(0.01)

    def process(self, text: str) -> dict:
        self.events.clear()
        self.path.clear()

        self.emit("INPUT", "User input received")

        # -------------------------
        # Childhood learning
        # -------------------------
        if self.development.STAGES[self.development.index] in ["Birth", "Learning"]:
            if not self.childhood.active:
                self.childhood.start_burst()
                self.emit("CHILDHOOD", "Learning burst started")

            self.childhood.absorb(text)

            if not self.childhood.is_active():
                self.emit("CHILDHOOD", "Learning burst ended")

        # -------------------------
        # Identity shortcuts
        # -------------------------
        if self.identity.is_user_introduction(text):
            self.emit("IDENTITY", "User identity detected")
            self.identity.capture_user(text)
            self.memory.add("identity", f"User is {self.identity.user_name}")

            self.last_coherence = self._coherence.score(
                mode="recognition",
                emotion_value=self.emotion.value,
                signals=None
            )

            self.emit("OUTPUT", "Identity stored")
            return self._result(
                f"Nice to meet you, {self.identity.user_name}.",
                None,
                "recognition"
            )

        if self.identity.is_system_identity_question(text):
            self.emit("IDENTITY", "System identity recognised")
            self.emit("THINKING", "Recognition processing")

            reasoning = self.multi_agent.run(text, mode="recognition")
            self.last_signals = reasoning["signals"]

            self.last_coherence = self._coherence.score(
                mode="recognition",
                emotion_value=self.emotion.value,
                signals=self.last_signals
            )

            self.emit("OUTPUT", "Identity answer ready")
            return self._result(
                self.identity.system_answer(),
                self.last_signals,
                "recognition"
            )

        # -------------------------
        # Emotion update
        # -------------------------
        self.emit("EMOTION", "Updating emotional state")
        self.emotion.update(text)

        # -------------------------
        # Deliberation (coherence-fed)
        # -------------------------
        coherence_hint = (
            self.last_coherence["score"]
            if self.last_coherence else None
        )

        self.emit("THINKING", "Deliberative reasoning (coherence-fed)")
        reasoning = self.multi_agent.run(
            text,
            mode="deliberation",
            coherence_hint=coherence_hint
        )

        self.last_signals = reasoning["signals"]

        # -------------------------
        # Memory + development
        # -------------------------
        self.emit("MEMORY", "Storing dialogue")
        self.memory.add("dialogue", text)

        self.emit("DEVELOPMENT", "Updating development stage")
        self.development.update(self.memory)

        # -------------------------
        # Coherence scoring (post)
        # -------------------------
        self.last_coherence = self._coherence.score(
            mode="deliberation",
            emotion_value=self.emotion.value,
            signals=self.last_signals
        )

        # -------------------------
        # Speech gate (unchanged)
        # -------------------------
        label = self.last_coherence["label"]

        if label == "RED":
            self.emit("GATE", "Speech blocked")
            answer = (
                "I’m not coherent enough to answer safely yet. "
                "Could you clarify or give one concrete example?"
            )
            self.emit("OUTPUT", "Stabiliser response ready")
            return self._result(answer, self.last_signals, "deliberation", "block")

        if label == "AMBER":
            self.emit("GATE", "Cautious speech")
            answer = reasoning["final"] + "\n\n(If you want a tighter answer, state your goal in one line.)"
            self.emit("OUTPUT", "Cautious answer ready")
            return self._result(answer, self.last_signals, "deliberation", "cautious")

        self.emit("GATE", "Speech allowed")
        self.emit("OUTPUT", "Answer ready")
        return self._result(reasoning["final"], self.last_signals, "deliberation", "speak")

    def _result(self, answer, signals, mode, speech_action="speak"):
        return {
            "answer": answer,
            "events": list(self.events),
            "path": list(self.path),
            "signals": signals,
            "mode": mode,
            "coherence": self.last_coherence,
            "speech_action": speech_action
        }
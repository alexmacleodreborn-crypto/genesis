import time


class A7DOMind:
    """
    Central cognitive orchestrator.
    NO code executes at import time.
    """

    def __init__(self, identity, emotion, memory, development, multi_agent, childhood):
        self.identity = identity
        self.emotion = emotion
        self.memory = memory
        self.development = development
        self.multi_agent = multi_agent
        self.childhood = childhood

        self.events = []

    # --------------------------------------------------
    # Internal logging
    # --------------------------------------------------

    def emit(self, phase: str, message: str):
        self.events.append(f"[{phase}] {message}")
        time.sleep(0.05)

    # --------------------------------------------------
    # Main cognitive cycle
    # --------------------------------------------------

    def process(self, text: str) -> dict:
        self.events.clear()

        self.emit("INPUT", "User input received")

        # ----------------------------------------------
        # Childhood learning (passive, stage-gated)
        # ----------------------------------------------

        if self.development.STAGES[self.development.index] in ["Birth", "Learning"]:
            if not self.childhood.active:
                self.childhood.start_burst()
                self.emit("CHILDHOOD", "Learning burst started")

            self.childhood.absorb(text)

            if not self.childhood.is_active():
                self.emit("CHILDHOOD", "Learning burst ended")

        # ----------------------------------------------
        # User identity capture
        # ----------------------------------------------

        if self.identity.is_user_introduction(text):
            self.emit("IDENTITY", "User identity detected")
            self.identity.capture_user(text)
            self.memory.add("identity", f"User is {self.identity.user_name}")
            self.emit("OUTPUT", "Identity stored")

            return self._result(
                f"Nice to meet you, {self.identity.user_name}.",
                {}
            )

        # ----------------------------------------------
        # System identity (recognition mode)
        # ----------------------------------------------

        if self.identity.is_system_identity_question(text):
            self.emit("IDENTITY", "System identity recognised")
            self.emit("THINKING", "Recognition processing")

            reasoning = self.multi_agent.run(text, mode="recognition")

            self.emit("OUTPUT", "Identity answer ready")

            return self._result(
                self.identity.system_answer(),
                reasoning["signals"]
            )

        # ----------------------------------------------
        # Emotion
        # ----------------------------------------------

        self.emit("EMOTION", "Updating emotional state")
        self.emotion.update(text)

        # ----------------------------------------------
        # Deliberative reasoning
        # ----------------------------------------------

        self.emit("THINKING", "Deliberative reasoning")
        reasoning = self.multi_agent.run(text, mode="deliberation")

        # ----------------------------------------------
        # Memory
        # ----------------------------------------------

        self.emit("MEMORY", "Storing dialogue")
        self.memory.add("dialogue", text)

        # ----------------------------------------------
        # Development
        # ----------------------------------------------

        self.emit("DEVELOPMENT", "Updating development stage")
        self.development.update(self.memory)

        self.emit("OUTPUT", "Answer ready")

        return self._result(
            reasoning["final"],
            reasoning["signals"]
        )

    # --------------------------------------------------
    # Output packaging
    # --------------------------------------------------

    def _result(self, answer, signals):
        return {
            "answer": answer,
            "events": list(self.events),
            "signals": signals
        }
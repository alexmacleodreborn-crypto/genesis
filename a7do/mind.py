import time

class A7DOMind:
    def __init__(self, identity, emotion, memory, development, multi_agent, childhood):
        self.identity = identity
        self.emotion = emotion
        self.memory = memory
        self.development = development
        self.multi_agent = multi_agent
        self.events = []

    def emit(self, phase: str, message: str):
        self.events.append(f"[{phase}] {message}")
        time.sleep(0.1)

    def process(self, text: str) -> dict:
        self.events.clear()
        self.emit("INPUT", "User input received")

# --------------------------------------------------
# Childhood learning (ages 0–5)
# --------------------------------------------------
if self.development.STAGES[self.development.index] in ["Birth", "Learning"]:
    if not self.childhood.active:
        self.childhood.start_burst()
        self.emit("CHILDHOOD", "Childhood learning burst started")

    self.childhood.absorb(text)

    if not self.childhood.is_active():
        self.emit("CHILDHOOD", "Childhood learning burst ended")
        
        # User identity capture
        if self.identity.is_user_introduction(text):
            self.emit("IDENTITY", "User introduced themselves")
            self.identity.capture_user(text)
            self.memory.add("identity", f"User is {self.identity.user_name}")
            self.emit("OUTPUT", "User identity stored")
            return self._result(f"Nice to meet you, {self.identity.user_name}.", {})

        # System identity
        if self.identity.is_system_identity_question(text):
            self.emit("IDENTITY", "System identity question")
            return self._result(self.identity.system_answer(), {})

        # Emotion
        self.emit("EMOTION", "Updating emotional state")
        self.emotion.update(text)

        # Reasoning
        self.emit("THINKING", "Running reasoning cycle")
        reasoning = self.multi_agent.run(text)

        # Memory
        self.emit("MEMORY", "Storing dialogue")
        self.memory.add("dialogue", text)

        # Development
        self.emit("DEVELOPMENT", "Updating development")
        self.development.update(self.memory)

        self.emit("OUTPUT", "Answer ready")
        return self._result(reasoning["final"], reasoning["signals"])

    def _result(self, answer, signals):
        return {
            "answer": answer,
            "events": self.events,
            "signals": signals
        }
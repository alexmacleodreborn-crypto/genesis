from dataclasses import dataclass, field
from typing import Dict, Any, List
import time

@dataclass
class CognitiveEvent:
    phase: str
    message: str
    payload: Dict[str, Any] = field(default_factory=dict)

class A7DOMind:
    def __init__(self, identity, emotion, memory, development, multi_agent):
        self.identity = identity
        self.emotion = emotion
        self.memory = memory
        self.development = development
        self.multi_agent = multi_agent

        self.events: List[CognitiveEvent] = []

    def emit(self, phase: str, message: str, **payload):
        self.events.append(CognitiveEvent(phase, message, payload))
        time.sleep(0.12)

    def process(self, user_input: str) -> Dict[str, Any]:
        self.events.clear()

        self.emit("INPUT", "User input received")

        # Identity gate
        if self.identity.is_identity_question(user_input):
            self.emit("IDENTITY", "Identity question detected")
            answer = self.identity.answer(user_input)
        else:
            self.emit("EMOTION", "Updating emotional baseline")
            self.emotion.update(user_input)

            self.emit("THINKING", "Running multi-agent reasoning")
            reasoning = self.multi_agent.run(user_input)

            answer = reasoning["final"]

        self.emit("MEMORY", "Storing episodic memory")
        self.memory.add(
            kind="dialogue",
            content=user_input,
            emotion=self.emotion.label
        )

        self.emit("DEVELOPMENT", "Updating developmental stage")
        self.development.update(self.memory)

        self.emit("OUTPUT", "Answer ready")

        return {
            "answer": answer,
            "events": self.events,
            "emotion": self.emotion.export(),
            "development": self.development.export(),
            "memory": self.memory.recent(),
            "reasoning": self.multi_agent.last_signals()
        }
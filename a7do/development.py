class Development:
    STAGES = [
        "Birth",
        "Learning",
        "Concept Formation",
        "Self Reflection",
        "Mature Reasoning"
    ]

    def __init__(self):
        self.index = 0

    def update(self, memory: "Memory"):
        if len(memory.entries) > (self.index + 1) * 5:
            self.index = min(self.index + 1, len(self.STAGES) - 1)

    def panel(self) -> str:
        return f"""
**Development**
- Stage: {self.STAGES[self.index]}
"""
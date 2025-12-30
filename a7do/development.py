class Development:
    STAGES = [
        "Birth",
        "Learning",
        "Concept Formation",
        "Self Reflection",
        "Mature Reasoning"
    ]

    def __init__(self):
        self.stage_index = 0

    def update(self, memory):
        if len(memory.entries) > (self.stage_index + 1) * 5:
            self.stage_index = min(self.stage_index + 1, len(self.STAGES) - 1)

    def export(self):
        return {"stage": self.STAGES[self.stage_index]}

    def character_panel(self) -> str:
        return f"""
**Development**
- Stage: {self.STAGES[self.stage_index]}
"""
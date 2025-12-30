class EmotionalState:
    def __init__(self):
        self.value = 0.0
        self.label = "neutral"

    def update(self, text: str):
        if "?" in text:
            self.value += 0.1
            self.label = "curious"
        else:
            self.value *= 0.95

    def export(self):
        return {"value": self.value, "label": self.label}

    def character_panel(self) -> str:
        return f"""
**Emotion**
- State: {self.label}
- Intensity: {self.value:.2f}
"""
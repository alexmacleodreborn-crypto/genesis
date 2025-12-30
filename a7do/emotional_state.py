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
        return {"value": round(self.value, 2), "label": self.label}

    def panel(self) -> str:
        return f"""
**Emotion**
- State: {self.label}
- Level: {self.value:.2f}
"""
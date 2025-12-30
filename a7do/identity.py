class Identity:
    def __init__(self):
        self.name = "A7DO"
        self.creator = "Alex Macleod"
        self.kind = "Artificial Cognitive System"

    def is_identity_question(self, text: str) -> bool:
        triggers = ["who are you", "your name", "what are you"]
        return any(t in text.lower() for t in triggers)

    def answer(self, _: str) -> str:
        return (
            f"I am {self.name}, a modular cognitive system created by "
            f"{self.creator}. I reason, remember, and develop over time."
        )

    def character_panel(self) -> str:
        return f"""
**Identity**
- Name: {self.name}
- Type: {self.kind}
- Creator: {self.creator}
"""
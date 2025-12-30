class Identity:
    def __init__(self):
        self.name = "A7DO"
        self.creator = "Alex Macleod"
        self.kind = "Artificial Cognitive System"

        # NEW
        self.user_name = None

    def is_identity_question(self, text: str) -> bool:
        triggers = ["who are you", "your name", "what are you"]
        return any(t in text.lower() for t in triggers)

    def is_user_introduction(self, text: str) -> bool:
        lowered = text.lower()
        return lowered.startswith("i am ") or "my name is" in lowered

    def capture_user_identity(self, text: str):
        lowered = text.lower()
        if lowered.startswith("i am "):
            self.user_name = text[5:].strip()
        elif "my name is" in lowered:
            self.user_name = text.split("my name is")[-1].strip()

    def answer(self, _: str) -> str:
        return (
            f"I am {self.name}, a modular cognitive system created by "
            f"{self.creator}."
        )

    def character_panel(self) -> str:
        user = self.user_name if self.user_name else "Unknown"
        return f"""
**Identity**
- Name: {self.name}
- Type: {self.kind}
- Creator: {self.creator}
- User: {user}
"""
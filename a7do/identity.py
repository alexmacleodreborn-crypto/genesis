class Identity:
    def __init__(self):
        self.system_name = "A7DO"
        self.creator = "Alex Macleod"
        self.user_name = None

    def is_system_identity_question(self, text: str) -> bool:
        t = text.lower()
        return any(x in t for x in ["who are you", "your name", "what are you"])

    def is_user_introduction(self, text: str) -> bool:
        t = text.lower()
        return t.startswith("i am ") or "my name is" in t

    def capture_user(self, text: str):
        t = text.lower()
        if t.startswith("i am "):
            self.user_name = text[5:].strip()
        elif "my name is" in t:
            self.user_name = text.split("my name is")[-1].strip()

    def system_answer(self) -> str:
        return (
            f"I am {self.system_name}, a modular cognitive system "
            f"created by {self.creator}."
        )

    def panel(self) -> str:
        return f"""
**Identity**
- System: {self.system_name}
- Creator: {self.creator}
- User: {self.user_name or "Unknown"}
"""
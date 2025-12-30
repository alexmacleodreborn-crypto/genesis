import re


class Identity:
    def __init__(self):
        self.user_name = None
        self.system_name = "A7DO"
        self.creator = "Alex Macleod"

    def is_user_introduction(self, text: str) -> bool:
        return bool(re.search(r"\b(my name is|i am|i'm)\b", text.lower()))

    def is_system_identity_question(self, text: str) -> bool:
        return bool(re.search(r"\b(who are you|what is your name)\b", text.lower()))

    def is_user_identity_question(self, text: str) -> bool:
        return bool(re.search(r"\b(who am i|what do you know about me|what am i like)\b", text.lower()))

    def capture_user(self, text: str):
        m = re.search(r"\b(my name is|i am|i'm)\s+([a-zA-Z]+)", text.lower())
        if m:
            self.user_name = m.group(2).capitalize()

    def system_answer(self) -> str:
        return f"I am {self.system_name}, a modular cognitive system created by {self.creator}."
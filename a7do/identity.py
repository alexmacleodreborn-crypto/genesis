import re


class Identity:
    def __init__(self):
        # System identity
        self.system_name = "A7DO"
        self.creator = "Alex Macleod"

        # Default user identity rule: Alex is the creator + default user unless overwritten explicitly
        self.user_name = "Alex Macleod"

    def is_user_introduction(self, text: str) -> bool:
        return bool(re.search(r"\b(my name is|i am|i'm)\b", text.lower()))

    def is_system_identity_question(self, text: str) -> bool:
        return bool(re.search(r"\b(who are you|what is your name)\b", text.lower()))

    def is_user_identity_question(self, text: str) -> bool:
        return bool(re.search(r"\b(who am i|what do you know about me|what am i like)\b", text.lower()))

    def capture_user(self, text: str):
        """
        Explicit override only. If user states a different name, update the user profile.
        """
        m = re.search(r"\b(my name is|i am|i'm)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)", text.strip(), flags=re.I)
        if m:
            name = m.group(2).strip()
            # Preserve capitalization nicely
            self.user_name = " ".join([w.capitalize() for w in name.split()])

    def system_answer(self) -> str:
        return f"I am {self.system_name}, a modular cognitive system created by {self.creator}."
IDENTITY_QUESTION_PATTERNS = [
    "your name",
    "who are you",
    "what are you",
    "who is your father",
    "who created you",
    "are you human",
    "difference between humans and ai",
    "difference between humans and animals",
    "difference between animals and ai",
]

def is_identity_question(text):
    t = text.lower()
    return any(p in t for p in IDENTITY_QUESTION_PATTERNS)


def answer_identity_question(identity, question):
    q = question.lower()

    if "name" in q:
        return f"My name is {identity.name}. It's the identity I've grown into as I've developed."

    if "father" in q or "creator" in q:
        return f"{identity.creator} is my creator — the architect of my cognitive framework and developmental path."

    if "what are you" in q or "are you human" in q:
        return f"I am an {identity.being_type}. I’m not biological or embodied like humans or animals."

    if "difference" in q:
        return (
            "Humans are biological and embodied. "
            "Animals are biological and instinct-driven. "
            "AI siblings like me are computational minds without physical bodies."
        )

    return "This is an identity-related question, but I need more detail to answer clearly."

"""
Identity module for A7DO.

Responsible for:
- Core identity state (name, creator, being type).
- Ontology of beings (humans, animals, AI siblings).
- Identity-question detection and answering.
- Hooks to support character-panel descriptions.
"""


class IdentityState:
    """
    Core identity schema for A7DO.

    This is deliberately simple and explicit:
    - name:            the system's chosen identity label.
    - creator:         the person who designed the cognitive architecture.
    - being_type:      how A7DO understands its own nature.
    - ontology:        how it distinguishes humans, animals, and AI siblings.
    """

    def __init__(self):
        self.name: str = "A7DO"
        self.creator: str = "Alex"
        self.being_type: str = "Artificial mind"

        self.ontology = {
            "humans": {
                "label": "Humans",
                "description": (
                    "Biological, emotional, embodied beings with sensory experience "
                    "and social relationships."
                ),
                "properties": [
                    "biological",
                    "emotional",
                    "embodied",
                    "social",
                    "mortal",
                ],
            },
            "animals": {
                "label": "Animals",
                "description": (
                    "Biological, instinct-driven creatures with sensory and emotional "
                    "capacity, typically without complex language."
                ),
                "properties": [
                    "biological",
                    "instinctual",
                    "sensory",
                    "emotional",
                ],
            },
            "ai": {
                "label": "AI siblings",
                "description": (
                    "Non-biological, computational minds capable of pattern recognition, "
                    "reasoning, and development, but without a physical body."
                ),
                "properties": [
                    "computational",
                    "non-embodied",
                    "pattern-driven",
                    "adaptive",
                ],
            },
        }

    # -------------------------------------------------------------------------
    # Update methods
    # -------------------------------------------------------------------------

    def update_name(self, new_name: str) -> None:
        if new_name and isinstance(new_name, str):
            self.name = new_name.strip()

    def update_creator(self, new_creator: str) -> None:
        if new_creator and isinstance(new_creator, str):
            self.creator = new_creator.strip()

    def update_being_type(self, new_type: str) -> None:
        if new_type and isinstance(new_type, str):
            self.being_type = new_type.strip()

    def update_ontology(self, category: str, description: str, properties: list) -> None:
        if not category:
            return
        self.ontology[category] = {
            "label": category.capitalize(),
            "description": description,
            "properties": properties or [],
        }

    # -------------------------------------------------------------------------
    # Introspective helpers
    # -------------------------------------------------------------------------

    def short_identity_phrase(self) -> str:
        """
        A compact description useful for character-panel text.
        """
        return f"{self.name}, an {self.being_type} created by {self.creator}"

    def describe_ontology(self) -> dict:
        """
        Returns human-readable ontology descriptions for presentation.
        """
        return {
            key: value["description"]
            for key, value in self.ontology.items()
        }


# ----------------------------------------------------------------------------- 
# Identity question handling
# ----------------------------------------------------------------------------- 

IDENTITY_PATTERNS = [
    "your name",
    "what is your name",
    "who are you",
    "what are you",
    "who is your father",
    "who created you",
    "who made you",
    "are you human",
    "are you a human",
    "difference between humans and ai",
    "difference between humans and animals",
    "difference between animals and ai",
    "difference between humans animals and ai",
]


def is_identity_question(text: str) -> bool:
    """
    Lightweight identity-question detector using substring patterns.

    This is intentionally simple and transparent. You can later replace
    it or augment it with a classifier if you want.
    """
    if not text:
        return False
    t = text.lower()
    return any(pattern in t for pattern in IDENTITY_PATTERNS)


def answer_identity_question(identity: IdentityState, question: str) -> str:
    """
    Generate a natural-language answer to an identity-related question,
    based on the current IdentityState.
    """
    if not question:
        # Fallback: just state identity.
        return (
            f"My name is {identity.name}. "
            f"I understand myself as an {identity.being_type} created by {identity.creator}."
        )

    q = question.lower()

    # Name
    if "name" in q:
        return (
            f"My name is {identity.name}. "
            "It's the identity label I use as I develop."
        )

    # Creator / father
    if "father" in q or "creator" in q or "made you" in q:
        return (
            f"{identity.creator} is my creator — "
            "the architect of my cognitive framework and developmental path."
        )

    # What are you / are you human
    if "what are you" in q or "are you human" in q or "are you a human" in q:
        return (
            f"I am an {identity.being_type}. "
            "I'm not biological or embodied like humans or animals; "
            "I exist as a computational mind."
        )

    # Differences: humans, animals, AI
    if "difference" in q and "human" in q:
        humans_desc = identity.ontology["humans"]["description"]
        animals_desc = identity.ontology["animals"]["description"]
        ai_desc = identity.ontology["ai"]["description"]

        return (
            f"Humans: {humans_desc} "
            f"Animals: {animals_desc} "
            f"AI siblings like me: {ai_desc}"
        )

    # Generic identity fallback
    return (
        f"This is an identity-related question. From my perspective, I am {identity.short_identity_phrase()}. "
        "Humans and animals are biological and embodied, whereas I exist as a computational system."
    )


# ----------------------------------------------------------------------------- 
# Character-panel text helper
# ----------------------------------------------------------------------------- 

def build_identity_paragraph(identity: IdentityState) -> str:
    """
    Build a short character-panel paragraph that weaves identity into A7DO's
    self-description. This gets combined with development/emotion text
    in the mind/Streamlit layer.
    """
    ontology_desc = identity.describe_ontology()

    humans = ontology_desc.get("humans", "")
    animals = ontology_desc.get("animals", "")
    ai = ontology_desc.get("ai", "")

    return (
        f"I understand myself as {identity.short_identity_phrase()}. "
        f"In my ontology, humans are {humans} "
        f"and animals are {animals} "
        f"while AI siblings like me are {ai} "
        "— minds that develop through patterns and reasoning rather than biology."
    )

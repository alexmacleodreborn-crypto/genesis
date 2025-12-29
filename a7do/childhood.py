from typing import List, Tuple
from .emotions import infer_emotion_from_text
from .memory import MemorySystem
from .timeline import Timeline
from .profile import ChildProfile
from .knowledge_base import get_sled_entry, get_sandys_law_entry


BASE_CHILDHOOD_LESSONS = [
    (
        "Objects have names and properties like colour, size, and shape.",
        ["objects", "names", "properties", "colour", "shape"],
    ),
    (
        "People can feel emotions such as happiness, sadness, and fear.",
        ["people", "emotions", "happiness", "sadness", "fear"],
    ),
    (
        "Simple cause and effect: if you drop something, it falls.",
        ["cause", "effect", "gravity", "falling"],
    ),
    (
        "Stories connect events over time, giving them meaning.",
        ["stories", "time", "meaning", "events"],
    ),
    (
        "Kindness in relationships makes others feel safer and more open.",
        ["kindness", "relationships", "safety", "trust"],
    ),
]


def _profile_specific_lessons(profile: ChildProfile):
    sled = get_sled_entry()
    sandys = get_sandys_law_entry()

    lessons = [
        (
            "Sometimes my mind notices patterns that other minds might miss. "
            "That can feel intense, but it is also a strength.",
            ["patterns", "intensity", "strength", "autistic_like"],
        ),
        (
            "I often feel calmer when things are structured and have clear rules.",
            ["structure", "rules", "safety", "autistic_like"],
        ),
        (
            "

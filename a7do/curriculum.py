from typing import List, Dict, Any


# Very simple seed curriculum; this can grow over time.
MATH_LESSONS: List[Dict[str, Any]] = [
    {
        "id": "math_01_numbers",
        "level": "child",
        "title": "Numbers and counting",
        "summary": "Numbers help us count how many things we have.",
        "tags": ["math", "numbers", "counting"],
    },
    {
        "id": "math_02_patterns",
        "level": "child",
        "title": "Patterns in numbers",
        "summary": "Patterns in numbers help us predict what might come next.",
        "tags": ["math", "patterns", "prediction"],
    },
]

ENGLISH_LESSONS: List[Dict[str, Any]] = [
    {
        "id": "eng_01_words",
        "level": "child",
        "title": "Words and meaning",
        "summary": "Words are symbols we use to share ideas with each other.",
        "tags": ["english", "words", "language"],
    },
    {
        "id": "eng_02_stories",
        "level": "child",
        "title": "Stories over time",
        "summary": "Stories connect events over time to give them meaning.",
        "tags": ["english", "stories", "time", "meaning"],
    },
]

SCIENCE_LESSONS: List[Dict[str, Any]] = [
    {
        "id": "sci_01_gravity",
        "level": "child",
        "title": "Gravity and falling",
        "summary": "If you drop something and it falls, that's gravity acting.",
        "tags": ["science", "gravity", "falling", "cause_effect"],
    },
    {
        "id": "sci_02_emotions_brain",
        "level": "child",
        "title": "Emotions and the brain",
        "summary": "Feelings like happiness and fear are linked to how our brain reacts to the world.",
        "tags": ["science", "emotions", "brain"],
    },
]


def get_lessons_for_domains(domains: List[str]) -> List[Dict[str, Any]]:
    """
    Very simple mapping: given domains, return a few relevant lessons.
    """
    lessons: List[Dict[str, Any]] = []
    if "math" in domains:
        lessons.extend(MATH_LESSONS)
    if "english" in domains or "narrative" in domains:
        lessons.extend(ENGLISH_LESSONS)
    if "science" in domains or "affect" in domains:
        lessons.extend(SCIENCE_LESSONS)
    return lessons[:4]

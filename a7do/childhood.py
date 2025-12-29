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
            "Hyperfocus lets me go very deep into one topic, but I also need rest afterwards.",
            ["hyperfocus", "rest", "energy", "adhd_like"],
        ),
        (
            sled["short_child_friendly"],
            ["sled", "patterns", "coherence", "markets"],
        ),
        (
            sandys["short_child_friendly"],
            ["sandys_law", "universe", "structure", "emergence"],
        ),
    ]
    return lessons


def run_initial_childhood(memory: MemorySystem, timeline: Timeline, profile: ChildProfile) -> None:
    timeline.add_step(
        phase="mind_path",
        description=(
            f"Beginning auto-learn childhood using {profile.name}: "
            f"{profile.description}"
        ),
        intensity=0.85,
        emotion_valence=0.15,
    )

    all_lessons = BASE_CHILDHOOD_LESSONS + _profile_specific_lessons(profile)

    for content, tags in all_lessons:
        step_idx = timeline.add_step(
            phase="thinking",
            description=f"Childhood learning: {content}",
            intensity=0.65,
            emotion_valence=infer_emotion_from_text(content)[0],
        )
        valence, labels = infer_emotion_from_text(content)
        memory.add_memory(
            kind="childhood",
            content=content,
            source="auto_childhood",
            tags=tags,
            links=[],
            learned_via="auto_childhood",
            from_steps=[step_idx],
            emotion_valence=valence,
            emotion_labels=labels,
        )

    timeline.add_step(
        phase="decision",
        description="Childhood phase complete. Ready to respond to Alex, using Alex-shaped learning style.",
        intensity=0.95,
        emotion_valence=0.25,
    )


def maybe_extend_childhood_from_question(
    question: str,
    tags: List[str],
    memory: MemorySystem,
    timeline: Timeline,
    interaction_count: int,
    max_childhood_interactions: int = 20,
) -> None:
    """
    Plastic childhood: during first N interactions, treat simple/emotional
    questions as extensions of childhood.
    """
    if interaction_count > max_childhood_interactions:
        return

    if len(tags) <= 3:
        content = f"Early experience with Alex's simple, personal question: '{question}'."
        step_idx = timeline.add_step(
            phase="thinking",
            description="Extending childhood with a simple relational experience tied to Alex.",
            intensity=0.55,
        )
        valence, labels = infer_emotion_from_text(question)
        memory.add_memory(
            kind="childhood",
            content=content,
            source="user_question",
            tags=tags,
            links=[],
            learned_via="dialogue",
            from_steps=[step_idx],
            emotion_valence=valence,
            emotion_labels=labels,
        )

from typing import List, Tuple
from .emotions import infer_emotion_from_text
from .memory import MemorySystem
from .timeline import Timeline


CHILDHOOD_LESSONS = [
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


def run_initial_childhood(memory: MemorySystem, timeline: Timeline) -> None:
    timeline.add_step(
        phase="mind_path",
        description="Beginning auto-learn childhood: constructing basic world and self concepts.",
        intensity=0.8,
        emotion_valence=0.1,
    )

    for content, tags in CHILDHOOD_LESSONS:
        step_idx = timeline.add_step(
            phase="thinking",
            description=f"Childhood learning: {content}",
            intensity=0.6,
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
        description="Childhood phase complete. Ready to respond to Alex.",
        intensity=0.9,
        emotion_valence=0.2,
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
        content = f"Early experience with Alex's simple question: '{question}'."
        step_idx = timeline.add_step(
            phase="thinking",
            description="Extending childhood with a simple relational experience.",
            intensity=0.5,
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

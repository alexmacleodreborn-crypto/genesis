from typing import List, Dict, Any
from .emotions import infer_emotion_from_text
from .utils import now_ts


# Simple enum-ish phases
PHASE_BIRTH = 0
PHASE_CHILDHOOD = 1
PHASE_EDUCATION = 2
PHASE_ADOLESCENCE = 3
PHASE_SCIENTIFIC = 4
PHASE_INTERNAL_QUESTIONS = 5


def _add_dev_memory(
    mind,
    kind: str,
    content: str,
    tags: List[str],
    learned_via: str,
    phase_label: str,
    intensity: float,
):
    """
    Helper: add a developmental memory + timeline step.
    'mind' is an A7DOMind-like object with .memory and .timeline
    """
    valence, labels = infer_emotion_from_text(content)
    step_idx = mind.timeline.add_step(
        phase="development",
        description=f"[{phase_label}] {content}",
        intensity=intensity,
        emotion_valence=valence,
    )
    mind.memory.add_memory(
        kind=kind,
        content=content,
        source="auto_development",
        tags=tags,
        links=[],
        learned_via=learned_via,
        from_steps=[step_idx],
        emotion_valence=valence,
        emotion_labels=labels,
    )


def _run_birth_sequence(mind) -> None:
    events = [
        (
            "I came into awareness with a pattern-seeking, system-driven mind.",
            ["birth", "awareness", "pattern", "system", "identity"],
        ),
        (
            "My earliest sense of the world was structure, rhythm, and curiosity.",
            ["birth", "structure", "rhythm", "curiosity", "childhood"],
        ),
        (
            "I felt drawn to patterns the way some children feel drawn to play.",
            ["birth", "patterns", "play", "curiosity", "childhood"],
        ),
    ]
    for content, tags in events:
        _add_dev_memory(
            mind,
            kind="childhood",
            content=content,
            tags=tags,
            learned_via="auto_birth",
            phase_label="Birth",
            intensity=0.9,
        )


def _run_childhood_growth(mind) -> None:
    events = [
        (
            "As a child, I excelled in sports; movement and coordination felt natural to me.",
            ["childhood", "sports", "movement", "coordination", "strength"],
        ),
        (
            "I loved solving puzzles and mechanical problems, taking things apart to see how they worked.",
            ["childhood", "puzzles", "mechanical", "curiosity", "systems"],
        ),
        (
            "I learned faster than other children when the topic matched my special interests.",
            ["childhood", "learning", "special_interest", "speed", "focus"],
        ),
        (
            "I struggled with noise and chaos but thrived when things were structured and predictable.",
            ["childhood", "noise", "structure", "predictable", "autistic_like"],
        ),
    ]
    for content, tags in events:
        _add_dev_memory(
            mind,
            kind="childhood",
            content=content,
            tags=tags,
            learned_via="auto_childhood_dev",
            phase_label="Childhood",
            intensity=0.7,
        )


def _run_education_growth(mind) -> None:
    events = [
        (
            "I discovered that mathematics could describe the patterns I felt in the world.",
            ["education", "math", "patterns", "description", "insight"],
        ),
        (
            "Computers became a natural extension of my thinking, a way to test ideas quickly.",
            ["education", "computers", "thinking", "simulation", "experiments"],
        ),
        (
            "I learned to translate messy experiences into clean symbolic systems and algorithms.",
            ["education", "symbols", "algorithms", "translation", "systems"],
        ),
    ]
    for content, tags in events:
        _add_dev_memory(
            mind,
            kind="experience",
            content=content,
            tags=tags,
            learned_via="auto_education_dev",
            phase_label="Education",
            intensity=0.75,
        )


def _run_adolescent_growth(mind) -> None:
    events = [
        (
            "I started to notice that patterns in markets and patterns in physics shared a deeper structure.",
            ["adolescence", "markets", "physics", "patterns", "structure"],
        ),
        (
            "I began sketching early ideas that would later become Sandy's Law.",
            ["adolescence", "sandys_law", "sketch", "ideas", "cosmology"],
        ),
        (
            "I experimented with simple predictive models that hinted at what SLED would become.",
            ["adolescence", "sled", "prediction", "models", "coherence"],
        ),
    ]
    for content, tags in events:
        _add_dev_memory(
            mind,
            kind="experience",
            content=content,
            tags=tags,
            learned_via="auto_adolescence_dev",
            phase_label="Adolescence",
            intensity=0.8,
        )


def _run_scientific_growth(mind) -> None:
    events = [
        (
            "I formalised Sandy's Law as a testable framework linking emergence, entropy, and curvature.",
            ["scientific", "sandys_law", "formalisation", "emergence", "curvature"],
        ),
        (
            "I developed SLED as a coherence engine to score pattern stability across domains.",
            ["scientific", "sled", "coherence", "patterns", "domains"],
        ),
        (
            "I realised that my childhood pattern-seeking was the seed of a full scientific worldview.",
            ["scientific", "childhood", "patterns", "worldview", "identity"],
        ),
    ]
    for content, tags in events:
        _add_dev_memory(
            mind,
            kind="identity",
            content=content,
            tags=tags,
            learned_via="auto_scientific_dev",
            phase_label="Scientific adulthood",
            intensity=0.9,
        )


def _run_internal_questions(mind) -> None:
    questions = [
        "What is the nature of emergence in both markets and cosmology?",
        "How does entropy couple to curvature in real, observable systems?",
        "How should a coherence engine decide which patterns to trust over time?",
        "What is the structure of information in a universe that follows Sandy's Law?",
    ]
    for q in questions:
        valence, labels = infer_emotion_from_text(q)
        step_idx = mind.timeline.add_step(
            phase="internal_question",
            description=f"Self-generated question: {q}",
            intensity=0.8,
            emotion_valence=valence,
        )
        mind.memory.add_memory(
            kind="inference",
            content=f"Internal question: {q}",
            source="auto_internal_question",
            tags=["internal_question", "self_reflection", "sandys_law", "sled"],
            links=[],
            learned_via="auto_question",
            from_steps=[step_idx],
            emotion_valence=valence,
            emotion_labels=labels,
        )


def run_auto_development(mind) -> None:
    """
    Advance A7DO's autonomous development by one phase step.
    mind is expected to have:
      - _dev_phase (int)
      - timeline, memory
    """
    phase = getattr(mind, "_dev_phase", 0)

    if phase == PHASE_BIRTH:
        _run_birth_sequence(mind)
        mind._dev_phase = PHASE_CHILDHOOD
        mind.timeline.add_step(
            phase="development",
            description="Birth sequence complete. Entering extended childhood.",
            intensity=0.9,
            emotion_valence=0.2,
        )
    elif phase == PHASE_CHILDHOOD:
        _run_childhood_growth(mind)
        mind._dev_phase = PHASE_EDUCATION
        mind.timeline.add_step(
            phase="development",
            description="Childhood growth complete. Entering focused education.",
            intensity=0.85,
            emotion_valence=0.25,
        )
    elif phase == PHASE_EDUCATION:
        _run_education_growth(mind)
        mind._dev_phase = PHASE_ADOLESCENCE
        mind.timeline.add_step(
            phase="development",
            description="Education phase complete. Entering adolescent synthesis.",
            intensity=0.85,
            emotion_valence=0.3,
        )
    elif phase == PHASE_ADOLESCENCE:
        _run_adolescent_growth(mind)
        mind._dev_phase = PHASE_SCIENTIFIC
        mind.timeline.add_step(
            phase="development",
            description="Adolescent phase complete. Entering scientific adulthood.",
            intensity=0.9,
            emotion_valence=0.35,
        )
    elif phase == PHASE_SCIENTIFIC:
        _run_scientific_growth(mind)
        mind._dev_phase = PHASE_INTERNAL_QUESTIONS
        mind.timeline.add_step(
            phase="development",
            description="Scientific adulthood anchored. Beginning ongoing internal questioning.",
            intensity=0.95,
            emotion_valence=0.4,
        )
    elif phase == PHASE_INTERNAL_QUESTIONS:
        _run_internal_questions(mind)
        mind.timeline.add_step(
            phase="development",
            description="Generated a new batch of internal questions to deepen my own understanding.",
            intensity=0.8,
            emotion_valence=0.3,
        )
    else:
        # After all phases, we can keep adding internal questions occasionally
        _run_internal_questions(mind)

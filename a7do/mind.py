"""
A7DO Mind Module — Full Orchestrator

This module coordinates:
- Identity system
- Emotional baseline system
- Memory system
- Multi-agent reasoning (Explorer / Critic / Integrator)
- Development stage logic
- Character panel generation

The Mind is the central cortex of A7DO.
"""

from __future__ import annotations
from typing import Dict, Any

# Subsystems
from .identity import (
    IdentityState,
    is_identity_question,
    answer_identity_question,
    build_identity_paragraph,
)

from .emotional_state import EmotionalState
from .multi_agent import run_multi_agent_cycle
from .development import (
    update_development_stage,
    build_development_paragraph,
)


class A7DOMind:
    """
    The central orchestrator for A7DO.

    Responsibilities:
    - Hold subsystem instances (identity, emotion, memory)
    - Process user questions
    - Trigger emotional updates
    - Trigger identity logic
    - Trigger multi-agent reasoning
    - Update development stage
    - Produce character-panel summaries
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self):
        # Core subsystems
        self.identity = IdentityState()
        self.emotional_state = EmotionalState()

        # Memory is attached later by Streamlit
        self.memory = None

        # Development stage
        self._development_stage = "Birth & Early Childhood"

        # Track last answer
        self._last_answer = None

    # ------------------------------------------------------------------
    # Memory injection
    # ------------------------------------------------------------------

    def attach_memory(self, memory_system):
        """
        Attach a MemorySystem instance after construction.
        """
        self.memory = memory_system

    # ------------------------------------------------------------------
    # Development stage accessor
    # ------------------------------------------------------------------

    def developmental_stage(self) -> str:
        return self._development_stage

    # ------------------------------------------------------------------
    # Core question-processing pipeline
    # ------------------------------------------------------------------

    def process_question(self, question: str) -> Dict[str, Any]:
        """
        Main entry point for handling user input.

        Pipeline:
        1. Detect identity questions
        2. Otherwise run multi-agent reasoning
        3. Update emotional baseline
        4. Store memory
        5. Update development stage
        6. Return structured answer
        """

        if not question:
            return {
                "answer": "I didn't receive a question.",
                "mode": "empty",
            }

        # --------------------------------------------------------------
        # 1. Identity questions
        # --------------------------------------------------------------
        if is_identity_question(question):
            answer = answer_identity_question(self.identity, question)

            # Emotional update
            self.emotional_state.update_from_valence(
                valence=0.1,
                label="curious",
                source="identity_question",
            )

            # Memory logging
            if self.memory:
                self.memory.add_memory(
                    kind="identity",
                    content=f"Identity question: {question}",
                    source="user",
                    tags=["identity", "self"],
                    emotion_valence=0.1,
                    emotion_label="curious",
                )

            # Development update
            update_development_stage(self)

            self._last_answer = answer
            return {
                "answer": answer,
                "mode": "identity",
            }

        # --------------------------------------------------------------
        # 2. Multi-agent reasoning (Explorer → Critic → Integrator)
        # --------------------------------------------------------------
        final_answer = run_multi_agent_cycle(question, self)

        # Emotional update (neutral baseline)
        self.emotional_state.update_from_valence(
            valence=0.0,
            label="neutral",
            source="dialogue",
        )

        # Memory logging
        if self.memory:
            self.memory.add_memory(
                kind="dialogue",
                content=question,
                source="user",
                tags=["dialogue"],
                emotion_valence=0.0,
                emotion_label="neutral",
            )

        # Development update
        update_development_stage(self)

        self._last_answer = final_answer
        return {
            "answer": final_answer,
            "mode": "dialogue",
        }

    # ------------------------------------------------------------------
    # Character panel summary
    # ------------------------------------------------------------------

    def build_character_panel(self) -> str:
        """
        Combine identity + emotional baseline + development into a
        coherent self-description paragraph.
        """

        identity_text = build_identity_paragraph(self.identity)
        emotion_text = self.emotional_state.build_emotional_paragraph()
        stage_name = self.developmental_stage()
        stage_text = build_development_paragraph(stage_name)

        return (
            f"### Identity\n{identity_text}\n\n"
            f"### Emotional State\n{emotion_text}\n\n"
            f"### Development\n{stage_text}"
        )

    # ------------------------------------------------------------------
    # Export for timeline/debugging
    # ------------------------------------------------------------------

    def export_state(self) -> Dict[str, Any]:
        """
        Export a compact snapshot of the mind for timeline logging.
        """
        return {
            "identity": {
                "name": self.identity.name,
                "creator": self.identity.creator,
                "being_type": self.identity.being_type,
            },
            "emotional_state": self.emotional_state.to_dict(),
            "development_stage": self._development_stage,
            "last_answer": self._last_answer,
        }

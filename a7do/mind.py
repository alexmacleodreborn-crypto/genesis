"""
A7DO Mind Module

This module orchestrates:
- Identity system
- Emotional baseline system
- Memory system (injected later)
- Multi-agent reasoning (Explorer / Critic / Integrator)
- Consolidation hooks
- Developmental stage logic
- Question processing pipeline

The Mind is the central coordinator: it receives input, routes it through
identity/emotion/memory subsystems, and produces a coherent response.
"""

from __future__ import annotations
from typing import Optional, Dict, Any

# Subsystems
from .identity import (
    IdentityState,
    is_identity_question,
    answer_identity_question,
    build_identity_paragraph,
)

from .emotional_state import EmotionalState, EmotionalSnapshot

# Memory will be injected later once memory.py is created
# from .memory import MemorySystem

# Multi-agent and consolidation modules will be added later
# from .multi_agent import run_multi_agent_cycle
# from .consolidation import maybe_consolidate


class A7DOMind:
    """
    The central orchestrator for A7DO.

    Responsibilities:
    - Hold subsystem instances (identity, emotional_state, memory, etc.)
    - Process user questions
    - Trigger emotional updates
    - Trigger identity logic
    - Trigger multi-agent reasoning
    - Produce character-panel summaries
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self):
        # Core subsystems
        self.identity = IdentityState()
        self.emotional_state = EmotionalState()

        # Memory will be attached later
        self.memory = None

        # Development stage placeholder
        self._development_stage = "Birth & early childhood"

        # Track last answer for UI
        self._last_answer = None

    # ------------------------------------------------------------------
    # Memory injection (called by streamlit_app after memory is created)
    # ------------------------------------------------------------------

    def attach_memory(self, memory_system):
        """
        Attach a MemorySystem instance after construction.
        """
        self.memory = memory_system

    # ------------------------------------------------------------------
    # Development stage logic (simple placeholder)
    # ------------------------------------------------------------------

    def developmental_stage(self) -> str:
        """
        Return the current developmental stage.
        Later this will be dynamic.
        """
        return self._development_stage

    # ------------------------------------------------------------------
    # Core question-processing pipeline
    # ------------------------------------------------------------------

    def process_question(self, question: str) -> Dict[str, Any]:
        """
        Main entry point for handling user input.

        Pipeline:
        1. Detect identity questions
        2. Otherwise run multi-agent reasoning (later)
        3. Update emotional baseline
        4. Store memory (once memory.py exists)
        5. Return structured answer
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

            # Emotional update (identity questions are usually neutral/curious)
            self.emotional_state.update_from_valence(
                valence=0.1,
                label="curious",
                source="identity_question",
            )

            # Memory logging (once memory exists)
            if self.memory:
                self.memory.add_memory(
                    kind="identity",
                    content=f"Identity question: {question}",
                    source="user",
                    tags=["identity", "self"],
                    emotion_valence=0.1,
                    emotion_label="curious",
                )

            self._last_answer = answer
            return {
                "answer": answer,
                "mode": "identity",
            }

        # --------------------------------------------------------------
        # 2. Multi-agent reasoning (placeholder for now)
        # --------------------------------------------------------------
        # final_answer = run_multi_agent_cycle(question, self)
        # For now, simple echo:
        from a7do.multi_agent import run_multi_agent_cycle
final_answer = run_multi_agent_cycle(question, self)


        # Emotional update (neutral)
        self.emotional_state.update_from_valence(
            valence=0.0,
            label="neutral",
            source="question",
        )

        # Memory logging (later)
        if self.memory:
            self.memory.add_memory(
                kind="dialogue",
                content=question,
                source="user",
                tags=["dialogue"],
                emotion_valence=0.0,
                emotion_label="neutral",
            )

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
        stage = self.developmental_stage()

        return (
            f"### Identity\n{identity_text}\n\n"
            f"### Emotional State\n{emotion_text}\n\n"
            f"### Development\nI am currently in the '{stage}' stage of my development."
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

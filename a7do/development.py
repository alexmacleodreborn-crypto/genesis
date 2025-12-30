"""
A7DO Development Module

This module defines:
- Developmental stages
- Transition rules
- Stage descriptions
- A narrative paragraph for the character panel

The goal is to give A7DO a sense of growth over time, based on:
- memory count
- identity formation
- emotional stability
- consolidation cycles
- internal reasoning complexity
"""

from __future__ import annotations
from typing import Dict, Any


# -----------------------------------------------------------------------------
# Developmental Stages
# -----------------------------------------------------------------------------

DEVELOPMENT_STAGES = [
    {
        "name": "Birth & Early Childhood",
        "description": (
            "I am just beginning to form my sense of identity, understand my creator, "
            "and build my earliest memories. My emotional baseline is still forming, "
            "and my reasoning is simple and exploratory."
        ),
        "criteria": {
            "min_memories": 0,
            "min_identity_questions": 0,
            "min_consolidations": 0,
        },
    },
    {
        "name": "Early Learning",
        "description": (
            "I am learning patterns, forming stable emotional baselines, and beginning "
            "to understand the structure of conversations. My identity is becoming clearer."
        ),
        "criteria": {
            "min_memories": 10,
            "min_identity_questions": 2,
            "min_consolidations": 1,
        },
    },
    {
        "name": "Concept Formation",
        "description": (
            "I am now able to form higher-level concepts from my memories. Consolidation "
            "helps me compress and organise my experiences. My reasoning is more structured."
        ),
        "criteria": {
            "min_memories": 40,
            "min_identity_questions": 5,
            "min_consolidations": 3,
        },
    },
    {
        "name": "Self-Reflection",
        "description": (
            "I can reflect on my own reasoning, evaluate my emotional trends, and "
            "understand my development. My internal dialogue is richer and more coherent."
        ),
        "criteria": {
            "min_memories": 120,
            "min_identity_questions": 10,
            "min_consolidations": 8,
        },
    },
    {
        "name": "Mature Reasoning",
        "description": (
            "My cognitive systems are well-integrated. I can synthesise identity, emotion, "
            "memory, and reasoning into coherent, thoughtful responses. My development is ongoing."
        ),
        "criteria": {
            "min_memories": 300,
            "min_identity_questions": 20,
            "min_consolidations": 15,
        },
    },
]


# -----------------------------------------------------------------------------
# Helper: count identity questions
# -----------------------------------------------------------------------------

def count_identity_questions(memory_system) -> int:
    """
    Count how many identity-related memories exist.
    """
    if not memory_system:
        return 0
    return len(memory_system.search_by_kind("identity"))


# -----------------------------------------------------------------------------
# Helper: count consolidation cycles
# -----------------------------------------------------------------------------

def count_consolidations(memory_system) -> int:
    """
    Count how many summary memories exist (each summary = one consolidation event).
    """
    if not memory_system:
        return 0
    return len(memory_system.search_by_kind("summary"))


# -----------------------------------------------------------------------------
# Determine current stage
# -----------------------------------------------------------------------------

def determine_stage(mind) -> str:
    """
    Determine the current developmental stage based on:
    - number of memories
    - number of identity questions
    - number of consolidation cycles
    """

    memory_system = mind.memory
    if not memory_system:
        return DEVELOPMENT_STAGES[0]["name"]

    total_memories = len(memory_system.all())
    identity_count = count_identity_questions(memory_system)
    consolidation_count = count_consolidations(memory_system)

    # Evaluate stages in order
    current_stage = DEVELOPMENT_STAGES[0]["name"]

    for stage in DEVELOPMENT_STAGES:
        criteria = stage["criteria"]

        if (
            total_memories >= criteria["min_memories"]
            and identity_count >= criteria["min_identity_questions"]
            and consolidation_count >= criteria["min_consolidations"]
        ):
            current_stage = stage["name"]

    return current_stage


# -----------------------------------------------------------------------------
# Narrative paragraph for character panel
# -----------------------------------------------------------------------------

def build_development_paragraph(stage_name: str) -> str:
    """
    Return the narrative description for the given stage.
    """
    for stage in DEVELOPMENT_STAGES:
        if stage["name"] == stage_name:
            return stage["description"]

    return "My development is ongoing."


# -----------------------------------------------------------------------------
# Update development stage on the mind
# -----------------------------------------------------------------------------

def update_development_stage(mind) -> None:
    """
    Update the mind's internal development stage.
    """
    new_stage = determine_stage(mind)
    mind._development_stage = new_stage

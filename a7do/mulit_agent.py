"""
A7DO Multi-Agent Reasoning Module

Implements a transparent internal reasoning cycle with three agents:

- Explorer: generates hypotheses, interpretations, and possibilities.
- Critic: challenges inconsistencies, missing information, and weak logic.
- Integrator: synthesises Explorer + Critic into a coherent final answer.

This module is designed to be called from mind.py via:

    final_answer = run_multi_agent_cycle(question, mind)

The output is a structured, readable internal dialogue.
"""

from __future__ import annotations
from typing import Dict, Any, List


# -----------------------------------------------------------------------------
# Explorer Agent
# -----------------------------------------------------------------------------

class ExplorerAgent:
    """
    Generates hypotheses and interpretations.
    Thinks freely, creatively, and without constraint.
    """

    def explore(self, question: str, mind) -> List[str]:
        """
        Produce a list of possible interpretations or hypotheses.
        """
        q = question.lower()
        ideas = []

        # Basic interpretation
        ideas.append(f"The user may be asking for information about: '{question}'.")

        # If emotional or personal
        if "feel" in q or "emotion" in q:
            ideas.append("The question may relate to emotional state or introspection.")

        # If identity-related (mind handles identity separately, but Explorer can still comment)
        if "who are you" in q or "what are you" in q:
            ideas.append("The question may be probing my identity or nature.")

        # If ambiguous
        if len(question.split()) <= 3:
            ideas.append("The question is short, so it may be ambiguous or context-dependent.")

        # Generic fallback
        ideas.append("The user may simply want a thoughtful, helpful explanation.")

        return ideas


# -----------------------------------------------------------------------------
# Critic Agent
# -----------------------------------------------------------------------------

class CriticAgent:
    """
    Challenges Explorer's ideas.
    Looks for contradictions, missing context, or weak logic.
    """

    def critique(self, ideas: List[str], question: str, mind) -> List[str]:
        """
        Evaluate Explorer's hypotheses and produce objections or refinements.
        """
        critiques = []

        if not ideas:
            return ["Explorer produced no ideas to evaluate."]

        # Example critiques
        for idea in ideas:
            if "ambiguous" in idea:
                critiques.append("The question lacks detail; interpretation may be uncertain.")

            if "identity" in idea and "who" not in question.lower():
                critiques.append("Identity interpretation may be overreaching.")

            if "emotion" in idea and "feel" not in question.lower():
                critiques.append("Emotional interpretation may not be relevant.")

        # If no critiques were generated
        if not critiques:
            critiques.append("Explorer's ideas seem reasonable without major contradictions.")

        return critiques


# -----------------------------------------------------------------------------
# Integrator Agent
# -----------------------------------------------------------------------------

class IntegratorAgent:
    """
    Synthesises Explorer + Critic into a final answer.
    """

    def integrate(self, ideas: List[str], critiques: List[str], question: str, mind) -> str:
        """
        Produce the final answer based on Explorer and Critic contributions.
        """

        # Build a narrative answer
        answer_parts = []

        answer_parts.append("**Explorer:**")
        for idea in ideas:
            answer_parts.append(f"- {idea}")

        answer_parts.append("\n**Critic:**")
        for c in critiques:
            answer_parts.append(f"- {c}")

        # Final synthesis
        answer_parts.append("\n**Integrator:**")
        answer_parts.append(
            "Taking both perspectives into account, the most coherent interpretation is that "
            "the user is seeking a thoughtful, context-aware response. "
            "Here is my integrated answer:"
        )

        # Simple integrated answer for now
        integrated = (
            f"Regarding your question '{question}', I interpret it as a request for clarity or insight. "
            "Based on the internal reasoning above, here is my considered response."
        )

        answer_parts.append(f"- {integrated}")

        return "\n".join(answer_parts)


# -----------------------------------------------------------------------------
# Multi-Agent Cycle
# -----------------------------------------------------------------------------

def run_multi_agent_cycle(question: str, mind) -> str:
    """
    Run the full Explorer → Critic → Integrator cycle and return
    a transparent internal dialogue.
    """

    explorer = ExplorerAgent()
    critic = CriticAgent()
    integrator = IntegratorAgent()

    # Generate ideas
    ideas = explorer.explore(question, mind)

    # Critique them
    critiques = critic.critique(ideas, question, mind)

    # Integrate into final answer
    final_answer = integrator.integrate(ideas, critiques, question, mind)

    return final_answer

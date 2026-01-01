from typing import Dict, Any

class CoherenceEngine:
    """
    Simple, strict grounding checks.
    - place must exist in homeplot rooms
    - agent must exist in world people/animals
    - parents must exist before non-parent learning events run
    """

    def evaluate(self, world, homeplot, ev) -> Dict[str, Any]:
        issues = []
        if not homeplot or not homeplot.rooms:
            issues.append("no_homeplot")

        if homeplot and ev.room not in homeplot.rooms:
            issues.append(f"unknown_room:{ev.room}")

        # agent must be in people or animals
        agent_ok = (ev.agent in world.people) or (ev.agent in world.animals)
        if not agent_ok:
            issues.append(f"unknown_agent:{ev.agent}")

        # early rule: parents must exist to unlock learning
        if not world.has_parents():
            issues.append("parents_missing")

        # object should exist if specified
        if ev.obj and (ev.obj not in world.objects):
            issues.append(f"unknown_object:{ev.obj}")

        score = 1.0 if not issues else max(0.0, 1.0 - 0.25 * len(issues))
        return {"score": round(score, 2), "issues": issues}
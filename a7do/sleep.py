from typing import Any, Dict, List
from a7do.reflection import ReflectionEngine


class SleepEngine:
    """
    Sleep = Consolidation + Reflection(Pattern1) + Confidence Decay
    Pattern1 is visual reoccurrence (no invented content).
    """
    def __init__(self):
        self.reflection = ReflectionEngine()
        self.last_sleep_report: Dict[str, Any] = {}

    def run_sleep(self, mind) -> Dict[str, Any]:
        # 1) Consolidation (phase placeholder; keep deterministic for now)
        consolidation = {"status": "ok", "note": "No compression yet (Pattern1 only)."}

        # 2) Reflection Pattern 1 (replay connected external day events)
        day_events: List[Dict[str, Any]] = getattr(mind, "day_external_events", [])
        reflection_report = self.reflection.run_pattern_1(day_events)

        # 3) Confidence reinforcement/decay
        reinf = self.reflection.reinforce_entities(mind.bridge.entities, reflection_report.get("node_freq", {}))

        report = {
            "consolidation": consolidation,
            "reflection": reflection_report,
            "confidence": reinf,
        }
        self.last_sleep_report = report
        return report
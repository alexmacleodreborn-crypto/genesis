from dataclasses import dataclass
from typing import List
from .utils import now_ts


@dataclass
class TimelineStep:
    step: int
    phase: str           # 'thinking', 'recall', 'cross_reference', 'decision', 'mind_path'
    description: str
    intensity: float     # 0–1
    emotion_valence: float
    timestamp: float


class Timeline:
    def __init__(self):
        self.steps: List[TimelineStep] = []

    def add_step(
        self,
        phase: str,
        description: str,
        intensity: float,
        emotion_valence: float = 0.0,
    ) -> int:
        step_idx = len(self.steps) + 1
        ts = now_ts()
        intensity = max(0.0, min(1.0, intensity))
        ev = max(-1.0, min(1.0, emotion_valence))
        step = TimelineStep(
            step=step_idx,
            phase=phase,
            description=description,
            intensity=intensity,
            emotion_valence=ev,
            timestamp=ts,
        )
        self.steps.append(step)
        return step_idx

    def to_records(self) -> List[dict]:
        return [
            {
                "step": s.step,
                "phase": s.phase,
                "description": s.description,
                "intensity": s.intensity,
                "emotion_valence": s.emotion_valence,
                "timestamp": s.timestamp,
            }
            for s in self.steps
        ]

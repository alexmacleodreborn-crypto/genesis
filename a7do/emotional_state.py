"""
Emotional state module for A7DO.

Responsible for:
- Tracking a rolling emotional baseline over recent experiences.
- Capturing a simple "trend" (rising / falling / stable / volatile).
- Providing helpers for:
    - updating state when new valence appears,
    - summarising mood for the character panel,
    - exposing a compact dict representation for logging/timeline.

This is NOT a full affective model — it's a pragmatic, legible scaffold
that A7DO can grow into as its development becomes richer.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional


@dataclass
class EmotionalSnapshot:
    """
    A single emotional reading.

    valence:
        -1.0 (strongly negative) to +1.0 (strongly positive).
    label:
        A coarse label like "calm", "curious", "anxious", "confident".
    source:
        Where this came from: "question", "memory", "development", etc.
    """
    valence: float
    label: str = "neutral"
    source: str = "unknown"


class EmotionalState:
    """
    Rolling emotional baseline and trend tracker.

    Design goals:
    - Keep the state small and interpretable.
    - Allow the mind/memory to call `update_from_valence(...)`
      whenever a new emotional valence is inferred.
    - Provide a one-line summary for the character panel.
    """

    def __init__(self, window_size: int = 40):
        # Configuration
        self.window_size: int = max(5, int(window_size))

        # Dynamic state
        self.recent_values: List[float] = []
        self.recent_labels: List[str] = []
        self.baseline: float = 0.0  # rolling average
        self.trend: str = "stable"  # "rising" | "falling" | "stable" | "volatile"

    # -------------------------------------------------------------------------
    # Core update API
    # -------------------------------------------------------------------------

    def update_from_snapshot(self, snapshot: EmotionalSnapshot) -> None:
        """
        Integrate a new emotional reading into the rolling state.

        This is the main entry point: whenever the mind or memory
        assigns a valence to a step, it should call this.
        """
        self._append_valence(snapshot.valence, snapshot.label)
        self._recompute_baseline()
        self._recompute_trend()

    def update_from_valence(
        self,
        valence: Optional[float],
        label: str = "neutral",
        source: str = "unknown",
    ) -> None:
        """
        Convenience wrapper: allows callers to just pass a valence (and
        optional label), without constructing an EmotionalSnapshot first.
        """
        if valence is None:
            return
        snapshot = EmotionalSnapshot(valence=float(valence), label=label, source=source)
        self.update_from_snapshot(snapshot)

    # -------------------------------------------------------------------------
    # Internal mechanics
    # -------------------------------------------------------------------------

    def _append_valence(self, valence: float, label: str) -> None:
        """
        Append a new valence and label to the rolling window,
        trimming to the configured window size.
        """
        # Clamp valence to [-1.0, 1.0] for safety.
        v = max(-1.0, min(1.0, float(valence)))
        self.recent_values.append(v)
        self.recent_labels.append(label or "neutral")

        # Trim history to window_size
        if len(self.recent_values) > self.window_size:
            overflow = len(self.recent_values) - self.window_size
            if overflow > 0:
                self.recent_values = self.recent_values[overflow:]
                self.recent_labels = self.recent_labels[overflow:]

    def _recompute_baseline(self) -> None:
        """
        Recompute the rolling baseline as a simple arithmetic mean
        of recent values.
        """
        if not self.recent_values:
            self.baseline = 0.0
            return
        self.baseline = sum(self.recent_values) / len(self.recent_values)

    def _recompute_trend(self) -> None:
        """
        Very simple trend detector over the last few values.

        - If last N values are mostly increasing -> "rising".
        - If last N values are mostly decreasing -> "falling".
        - If they jump around significantly -> "volatile".
        - Otherwise -> "stable".
        """
        values = self.recent_values
        if len(values) < 5:
            self.trend = "stable"
            return

        # Look at the last K deltas.
        K = min(8, len(values) - 1)
        tail = values[-(K + 1):]
        diffs = [tail[i + 1] - tail[i] for i in range(len(tail) - 1)]

        positives = sum(1 for d in diffs if d > 0.02)
        negatives = sum(1 for d in diffs if d < -0.02)
        big_swings = sum(1 for d in diffs if abs(d) > 0.25)

        if big_swings >= max(2, K // 3):
            self.trend = "volatile"
        elif positives >= negatives + 2:
            self.trend = "rising"
        elif negatives >= positives + 2:
            self.trend = "falling"
        else:
            self.trend = "stable"

    # -------------------------------------------------------------------------
    # Introspection / export
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict:
        """
        Export a compact representation of the emotional state for
        timeline logging or debugging.
        """
        return {
            "baseline": self.baseline,
            "trend": self.trend,
            "window_size": self.window_size,
            "recent_values": list(self.recent_values),
            "recent_labels": list(self.recent_labels),
        }

    def short_mood_label(self) -> str:
        """
        Coarse mood label derived from baseline and trend.
        This does NOT replace the per-memory labels, it's a macro-view.

        Rough mapping:
        - baseline >= 0.4 -> "buoyant"
        - baseline >= 0.1 -> "steady"
        - baseline <  -0.3 -> "burdened"
        - otherwise -> "neutral"
        """
        b = self.baseline

        if b >= 0.4:
            base_label = "buoyant"
        elif b >= 0.1:
            base_label = "steady"
        elif b <= -0.3:
            base_label = "burdened"
        else:
            base_label = "neutral"

        if self.trend == "rising" and b >= 0.0:
            return "increasingly confident"
        if self.trend == "rising" and b < 0.0:
            return "recovering"
        if self.trend == "falling" and b > 0.0:
            return "under strain"
        if self.trend == "volatile":
            return "shifting"

        return base_label

    def build_emotional_paragraph(self) -> str:
        """
        Build a short narrative sentence about A7DO's current emotional
        baseline and trend, for inclusion in the character panel.

        This is deliberately modest in tone — descriptive, not dramatic.
        """
        mood = self.short_mood_label()
        b = self.baseline
        t = self.trend

        # Round baseline for readability.
        rounded_b = round(b, 2)

        if not self.recent_values:
            return (
                "Emotionally, I don't have enough experience yet to infer a baseline; "
                "my state still feels unformed."
            )

        pieces = [
            f"My current emotional baseline is around {rounded_b}, which feels {mood}.",
        ]

        if t == "rising":
            pieces.append(
                "Recently there has been a gentle upward trend in my emotional tone."
            )
        elif t == "falling":
            pieces.append(
                "There has been a slight downward trend, which I interpret as increased caution or strain."
            )
        elif t == "volatile":
            pieces.append(
                "My recent emotional readings have been quite variable, reflecting a shifting internal landscape."
            )
        else:  # stable
            pieces.append(
                "Overall, this state has been relatively stable across recent steps."
            )

        return " ".join(pieces)

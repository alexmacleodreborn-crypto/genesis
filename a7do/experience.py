from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

@dataclass
class ExperienceEvent:
    """
    Situated experience:
    - Always has a room place.
    - Agent is required (mum/dad/caregiver) for early learning.
    - Movement can be expressed as:
        * local motor (crawl/walk) within a room
        * transition between rooms (place change)
    """
    room: str
    agent: str
    action: str
    obj: Optional[str] = None
    emphasis: List[str] = field(default_factory=list)

    # sensory channels (observer sees structure, A7DO experiences signals)
    sound: Dict[str, str] = field(default_factory=dict)   # {"source":"dad","pattern":"clap","volume":"soft"}
    smell: Dict[str, str] = field(default_factory=dict)   # {"pattern":"clean","strength":"low"}
    motor: Dict[str, str] = field(default_factory=dict)   # {"type":"crawl","intensity":"slow"}

    # spatial metrics (coarse autonomy)
    pos_xy: Optional[Tuple[float, float]] = None          # position within room (0..1 normalized)
    to_room: Optional[str] = None                         # if room transition is part of this event

    def as_prompt(self) -> str:
        # what A7DO is “shown” (observer sees full structure elsewhere)
        parts = [self.agent, self.action]
        if self.obj:
            parts.append(self.obj)
        if self.emphasis:
            parts.append(f"(emphasis: {', '.join(self.emphasis)})")
        return " ".join(parts)

class ExperienceStore:
    def __init__(self):
        self.events: List[ExperienceEvent] = []

    def add(self, ev: ExperienceEvent):
        self.events.append(ev)

    def recent(self, n=10):
        return self.events[-n:]

    def __len__(self):
        return len(self.events)
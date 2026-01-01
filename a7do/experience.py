import time
from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class Experience:
    experience_id: str
    place: str
    object_label: str
    interaction: Optional[str] = None
    visual: Optional[str] = None
    emotion: Optional[str] = None
    action: Optional[str] = None
    preference: Optional[str] = None
    created_at: float = 0.0


class ExperienceStore:
    def __init__(self):
        self.experiences: Dict[str, Experience] = {}

    def has_place(self, place: str) -> bool:
        return any(e.place == place for e in self.experiences.values())

    def has_place_object(self, place: str, obj: str) -> bool:
        return any((e.place == place and e.object_label == obj) for e in self.experiences.values())

    def create(self, place: str, object_label: str) -> Experience:
        eid = f"{place}:{object_label}:{int(time.time()*1000)}"
        exp = Experience(experience_id=eid, place=place, object_label=object_label, created_at=time.time())
        self.experiences[eid] = exp
        return exp
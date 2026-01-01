from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class PlaceProfile:
    name: str
    level: int = 0
    purpose: str = "room"
    features: List[str] = field(default_factory=list)  # bed, window, curtains
    sounds: List[str] = field(default_factory=list)    # hum, quiet
    smells: List[str] = field(default_factory=list)    # clean, soap
    wall_colour: str = "neutral"
    windows: int = 1

@dataclass
class PersonProfile:
    name: str
    role: str  # mum, dad, caregiver
    voice: str = "soft"
    typical_actions: List[str] = field(default_factory=list)

@dataclass
class AnimalProfile:
    name: str
    species: str
    temperament: str = "calm"
    sounds: List[str] = field(default_factory=list)

@dataclass
class ObjectProfile:
    name: str
    category: str  # toy, furniture, tool, container
    attributes: List[str] = field(default_factory=list)   # red, round
    affordances: List[str] = field(default_factory=list)  # roll, throw, catch
    container_of: Optional[str] = None  # if this object is a container, what it can hold

class WorldProfiles:
    """
    Observer-controlled reality catalog.
    A7DO never edits this directly.
    """

    def __init__(self):
        self.places: Dict[str, PlaceProfile] = {}
        self.people: Dict[str, PersonProfile] = {}
        self.animals: Dict[str, AnimalProfile] = {}
        self.objects: Dict[str, ObjectProfile] = {}

        # home scaffold settings
        self.home_seed: int = 42
        self.home_generated: bool = False

    def has_parents(self) -> bool:
        roles = {p.role.lower() for p in self.people.values()}
        return ("mum" in roles) and ("dad" in roles)

    def snapshot(self):
        return {
            "home_seed": self.home_seed,
            "home_generated": self.home_generated,
            "places": list(self.places.keys()),
            "people": [f"{p.name} ({p.role})" for p in self.people.values()],
            "animals": [f"{a.name} ({a.species})" for a in self.animals.values()],
            "objects": [f"{o.name} ({o.category})" for o in self.objects.values()],
        }
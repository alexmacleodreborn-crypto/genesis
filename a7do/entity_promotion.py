import re
import time
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ----------------------------
# Lightweight data structures
# ----------------------------

@dataclass
class PendingEntity:
    name: str
    kind_guess: str = "unknown"      # person | animal | object | unknown
    relation_hint: str = ""          # e.g. "my dog"
    owner_name: str = ""             # e.g. "Alex Macleod"
    count: int = 0
    confidence: float = 0.0
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    contexts: List[str] = field(default_factory=list)


@dataclass
class Entity:
    entity_id: str
    name: str
    kind: str = "unknown"
    owner_name: str = ""
    aliases: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


class EntityPromotionBridge:
    """
    Bridges linguistic recognition → entity binding with confidence + gates.

    Key idea:
    - We *observe* candidates from language
    - We accumulate confidence via recurrence
    - We only *promote* (bind) when rules indicate enough support
    - We never invent facts; we only bind a referent entity
    """

    QUESTION_WORDS = {"who", "what", "where", "when", "why", "how"}
    ROLE_WORDS = {"i", "me", "my", "mine", "you", "your", "yours", "we", "us", "our", "ours"}
    STOPWORDS = {
        "a", "an", "the", "and", "or", "but", "to", "of", "in", "on", "at", "with",
        "is", "are", "was", "were", "be", "been", "being",
        "this", "that", "these", "those"
    }

    ANIMAL_HINTS = {"dog", "cat", "puppy", "kitten", "horse", "rabbit", "parrot", "hamster"}

    def __init__(self):
        self._entities: Dict[str, Entity] = {}
        self._name_to_id: Dict[str, str] = {}
        self._pending: Dict[str, PendingEntity] = {}
        self._counter = 0

    # ----------------------------
    # Public views
    # ----------------------------

    @property
    def entities(self) -> Dict[str, Entity]:
        return self._entities

    @property
    def pending(self) -> Dict[str, PendingEntity]:
        return self._pending

    def find_entity_id(self, name: str) -> Optional[str]:
        if not name:
            return None
        return self._name_to_id.get(name.strip().lower())

    def describe(self, name: str) -> Optional[str]:
        eid = self.find_entity_id(name)
        if not eid:
            return None
        e = self._entities[eid]
        if e.kind == "animal" and e.owner_name:
            return f"{e.name} is an animal (likely a pet) associated with {e.owner_name}."
        if e.kind == "person":
            return f"{e.name} is a person in your world-model."
        return f"{e.name} is an entity in your world-model."

    # ----------------------------
    # Core: Observe → Pending → Promote
    # ----------------------------

    def observe(self, text: str, owner_name: str = "") -> Tuple[List[str], List[str], List[str]]:
        """
        Returns:
          - tags_to_add (list[str])  e.g. ["entity:animal:Xena"]
          - events (list[str])       human readable bridge events
          - questions (list[str])    what A7DO should ask to confirm if needed
        """
        tags_to_add: List[str] = []
        events: List[str] = []
        questions: List[str] = []

        # 1) High-confidence patterns (ownership + naming)
        # e.g. "my dog is called Xena", "my dog named Xena", "my dog is Xena"
        m = re.search(
            r"\bmy\s+(dog|cat|puppy|kitten|horse|rabbit|parrot|hamster)\s+(?:is\s+called|called|named|is)\s+([A-Z][a-zA-Z0-9_-]{1,30})\b",
            text
        )
        if m:
            animal = m.group(1).lower()
            name = m.group(2).strip()
            events.append(f"[BRIDGE] strong-pattern: my {animal} → {name}")
            self._observe_candidate(
                name=name,
                kind_guess="animal",
                relation_hint=f"my {animal}",
                owner_name=owner_name,
                context="ownership+naming"
            )

            # Strong pattern can promote immediately
            promoted_tag = self._maybe_promote(name, force=True)
            if promoted_tag:
                tags_to_add.append(promoted_tag)
                events.append(f"[BRIDGE] promoted: {name}")
            return tags_to_add, events, questions

        # 2) Soft proper-noun candidates (capitalised tokens)
        # We never auto-promote these; we only accumulate recurrence.
        tokens = re.findall(r"[A-Za-z][A-Za-z0-9_-]*", text)
        if tokens:
            # ignore interrogative if it's the first word capitalised (Who/What etc.)
            first = tokens[0].lower()
            for t in tokens:
                if not t or not t[0].isupper():
                    continue
                tl = t.lower()
                if tl in self.QUESTION_WORDS or tl in self.ROLE_WORDS or tl in self.STOPWORDS:
                    continue
                if first in self.QUESTION_WORDS and t == tokens[0]:
                    continue

                self._observe_candidate(
                    name=t,
                    kind_guess="unknown",
                    relation_hint="",
                    owner_name=owner_name,
                    context="capitalised_token"
                )
                events.append(f"[BRIDGE] observed candidate: {t}")

        # 3) If any pending crosses threshold, ask for confirmation (do not force)
        for pname, p in list(self._pending.items()):
            if p.confidence >= 0.70 and not self.find_entity_id(p.name):
                questions.append(
                    f"I’m learning that **{p.name}** is a recurring name. "
                    f"Who is {p.name} to you (person, pet, object)?"
                )

        return tags_to_add, events, questions

    # ----------------------------
    # Internals
    # ----------------------------

    def _observe_candidate(
        self,
        name: str,
        kind_guess: str,
        relation_hint: str,
        owner_name: str,
        context: str
    ):
        key = name.strip().lower()
        if not key:
            return

        # Already a bound entity → nothing to do
        if key in self._name_to_id:
            return

        p = self._pending.get(key)
        if not p:
            p = PendingEntity(
                name=name.strip(),
                kind_guess=kind_guess,
                relation_hint=relation_hint,
                owner_name=owner_name
            )
            self._pending[key] = p

        p.count += 1
        p.last_seen = time.time()
        if context not in p.contexts:
            p.contexts.append(context)

        # Confidence rises with recurrence; saturates to 1.0
        p.confidence = 1.0 - math.exp(-p.count / 3.0)

        # If we learned a stronger guess later, keep the strongest
        if kind_guess != "unknown":
            p.kind_guess = kind_guess
        if relation_hint:
            p.relation_hint = relation_hint
        if owner_name:
            p.owner_name = owner_name

    def _maybe_promote(self, name: str, force: bool = False) -> Optional[str]:
        key = name.strip().lower()
        if key in self._name_to_id:
            return None

        p = self._pending.get(key)
        if not p:
            return None

        # Gate: either strong evidence (force) or enough confidence + hint
        if not force:
            if p.confidence < 0.85:
                return None
            if p.kind_guess == "unknown":
                return None

        self._counter += 1
        eid = f"ENT_{self._counter:05d}"
        entity = Entity(
            entity_id=eid,
            name=p.name,
            kind=p.kind_guess,
            owner_name=p.owner_name
        )

        self._entities[eid] = entity
        self._name_to_id[key] = eid

        # Once promoted, keep pending entry but it’s now “resolved”
        return f"entity:{entity.kind}:{entity.name}"
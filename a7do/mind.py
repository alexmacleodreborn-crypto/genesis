import re
import time

from a7do.identity import Identity
from a7do.language import LanguageModule
from a7do.entity_promotion import EntityPromotionBridge
from a7do.relationships import RelationshipStore
from a7do.objects import ObjectManager
from a7do.event_graph import EventGraph
from a7do.sensory import SensoryParser
from a7do.memory import Memory
from a7do.tagger import Tagger
from a7do.experience import ExperienceStore
from a7do.recall import RecallEngine


PLACES = ["park", "home", "garden", "vet", "beach", "gate", "street"]
OBJECTS = ["swing", "ball", "toy", "stick", "box"]
COLOURS = ["red", "blue", "orange", "green", "yellow"]
KIN = ["uncle", "aunt", "brother", "sister", "mother", "father", "mum", "mom", "dad", "cousin"]


class A7DOMind:
    def __init__(self):
        self.identity = Identity()
        self.language = LanguageModule()
        self.bridge = EntityPromotionBridge()
        self.relationships = RelationshipStore()
        self.objects = ObjectManager()
        self.events = EventGraph()
        self.events_graph = self.events  # compatibility alias
        self.sensory = SensoryParser()
        self.memory = Memory()
        self.tagger = Tagger()
        self.experiences = ExperienceStore()

        # ensure agent exists
        self.agent = self.bridge.confirm_entity("A7DO", "agent", confidence=1.0, origin="system")

        # recall engine
        self.recall = RecallEngine(self.events, self.bridge.entities, self.objects, self.relationships, self.experiences)

        # dialogue state
        self.awaiting = None

    # ---------- helpers ----------
    def _speaker_name(self):
        return self.language.speaker() or self.identity.creator

    def _speaker(self):
        return self.bridge.confirm_entity(self._speaker_name(), "person", confidence=1.0, origin="user")

    def _extract_place(self, text_l):
        for p in PLACES:
            if p in text_l:
                return p
        return None

    def _extract_object(self, text_l):
        for o in OBJECTS:
            if re.search(rf"\b{o}\b", text_l):
                return o
        return None

    def _extract_colour(self, text_l):
        for c in COLOURS:
            if re.search(rf"\b{c}\b", text_l):
                return c
        return None

    # ---------- experience question chain (place-first gating already done) ----------
    def _experience_questions(self, exp):
        q4 = None
        q3 = {"type": "experience", "exp": exp, "field": "preference", "question": "Did I like it?", "next": q4}
        q2 = {"type": "experience", "exp": exp, "field": "action", "question": "What did you do?", "next": q3}
        q1 = {"type": "experience", "exp": exp, "field": "emotion", "question": "How did you feel?", "next": q2}
        q0v = {"type": "experience", "exp": exp, "field": "visual", "question": "What did it look like?", "next": q1}
        q0 = {"type": "experience", "exp": exp, "field": "interaction", "question": "How did you use it?", "next": q0v}
        return q0

    # ---------- main ----------
    def process(self, text: str):
        now = time.time()
        text = (text or "").strip()
        text_l = text.lower()
        tags = self.tagger.tag(text)

        speaker = self._speaker()

        self.memory.add(kind="utterance", content=text, timestamp=now, tags=tags)

        # ----- awaiting: experience Q/A -----
        if self.awaiting and self.awaiting.get("type") == "experience":
            exp = self.awaiting["exp"]
            field = self.awaiting["field"]
            setattr(exp, field, text)
            nxt = self.awaiting["next"]
            if nxt:
                self.awaiting = nxt
                return {"answer": nxt["question"], "tags": tags, "mode": "experience"}
            self.awaiting = None
            return {"answer": "Okay — I remember that experience.", "tags": tags, "mode": "experience"}

        # ----- awaiting: place confirmation (place-first) -----
        if self.awaiting and self.awaiting.get("type") == "confirm_place":
            place = self.awaiting["place"]
            obj = self.awaiting["object"]
            ans = text_l.strip()
            if ans in ("yes", "y"):
                exp = self.experiences.create(place, obj)
                self.awaiting = self._experience_questions(exp)
                return {"answer": f"Got it. Let's learn the {obj} at this {place}. " + self.awaiting["question"], "tags": tags, "mode": "experience"}
            if ans in ("no", "n"):
                exp = self.experiences.create(place, obj)
                self.awaiting = self._experience_questions(exp)
                return {"answer": f"Okay — new {place}. Let's learn the {obj} here. " + self.awaiting["question"], "tags": tags, "mode": "experience"}
            return {"answer": "Please answer yes or no.", "tags": tags, "mode": "experience"}

        # ----- awaiting: object ambiguity (yes/no then colour) -----
        if self.awaiting and self.awaiting.get("type") == "obj_disambiguate":
            ans = text_l.strip()
            if ans in ("yes", "y"):
                obj = self.objects.objects.get(self.awaiting["candidate_id"])
                self.awaiting = None
                if obj:
                    return {"answer": f"Okay — the {(obj.colour + ' ') if obj.colour else ''}{obj.label}.", "tags": tags, "mode": "object"}
                return {"answer": "Okay.", "tags": tags, "mode": "object"}
            if ans in ("no", "n"):
                self.awaiting = {"type": "obj_colour", "label": self.awaiting["label"]}
                return {"answer": "Which one is it? (say a colour like: orange)", "tags": tags, "mode": "object"}
            return {"answer": "Please answer yes or no.", "tags": tags, "mode": "object"}

        if self.awaiting and self.awaiting.get("type") == "obj_colour":
            label = self.awaiting["label"]
            colour = self._extract_colour(text_l) or text.strip().lower()
            obj = self.objects.create(label, colour=colour, owner_entity_id=speaker.entity_id)
            self.awaiting = None
            return {"answer": f"Okay — created a {colour} {label}.", "tags": tags, "mode": "object"}

        # =========================
        # 1) Recall queries (early)
        # =========================
        m = re.match(r"^\s*where\s+is\s+(the\s+)?(?:(red|blue|orange|green|yellow)\s+)?(swing|ball|toy|stick|box)\s*\??\s*$", text_l)
        if m:
            colour = m.group(2)
            label = m.group(3)
            return {"answer": self.recall.where_is_object(label, colour=colour), "tags": tags, "mode": "recall"}

        m = re.match(r"^\s*what\s+(?:(swing|ball|toy|stick|box)s?)\s+do\s+i\s+have\s*\??\s*$", text_l)
        if m:
            label = m.group(1)
            return {"answer": self.recall.what_objects_do_i_have(speaker.entity_id, label=label), "tags": tags, "mode": "recall"}

        m = re.match(r"^\s*do\s+i\s+have\s+(a\s+)?(?:(red|blue|orange|green|yellow)\s+)?(swing|ball|toy|stick|box)\s*\??\s*$", text_l)
        if m:
            colour = m.group(2)
            label = m.group(3)
            return {"answer": self.recall.do_i_have_object(speaker.entity_id, label, colour=colour), "tags": tags, "mode": "recall"}

        m = re.match(r"^\s*what\s+does\s+([a-z]+)\s+have\s*\??\s*$", text_l)
        if m:
            name = m.group(1).strip()
            ent = self.bridge.find_entity(name)
            if not ent:
                return {"answer": f"I don't know who {name} is yet.", "tags": tags, "mode": "recall"}
            return {"answer": self.recall.what_does_entity_have(ent.entity_id), "tags": tags, "mode": "recall"}

        m = re.match(r"^\s*what\s+do\s+i\s+remember\s+about\s+the\s+(park|home|garden|vet|beach|gate|street)\s*\??\s*$", text_l)
        if m:
            place = m.group(1)
            return {"answer": self.recall.experiences_at_place(place), "tags": tags, "mode": "recall"}

        # =========================
        # 2) Identity / speaker lock
        # =========================
        m = re.match(r"^\s*(my\s+name\s+is|i\s+am|i'm)\s+(.+?)\s*[.!?]*$", text_l)
        if m:
            name = m.group(2).strip().title()
            self.language.lock_speaker(name)
            self.identity.creator = name
            self.bridge.confirm_entity(name, "person", confidence=1.0, origin="declared")
            return {"answer": f"Locked. You are {name}.", "tags": tags, "mode": "identity"}

        if re.match(r"^\s*who\s+am\s+i\s*\??\s*$", text_l):
            return {"answer": f"You are {self._speaker_name()}.", "tags": tags, "mode": "identity"}

        # =========================
        # 3) Declarative: pet
        # =========================
        m = re.match(r"^\s*(.+?)\s+is\s+my\s+dog\s*[.!?]*$", text_l)
        if m:
            pet_name = m.group(1).strip().title()
            dog = self.bridge.confirm_entity(pet_name, "pet", confidence=1.0, origin="declared")
            self.relationships.add(speaker.entity_id, dog.entity_id, "pet", "ownership")
            return {"answer": f"Noted. {pet_name} is your dog.", "tags": tags, "mode": "relationship"}

        # =========================
        # 4) Declarative: kinship my/your
        # =========================
        m = re.match(r"^\s*(.+?)\s+is\s+(my|your)\s+(" + "|".join(KIN) + r")\s*[.!?]*$", text_l)
        if m:
            other_name = m.group(1).strip().title()
            who = m.group(2).lower()
            rel = m.group(3).lower()
            other = self.bridge.confirm_entity(other_name, "person", confidence=1.0, origin="declared")
            subject = speaker if who == "my" else self.agent
            self.relationships.add(subject.entity_id, other.entity_id, rel, f"{who}-kinship")
            return {"answer": f"Noted. {other_name} is {'your' if who=='my' else 'my'} {rel}.", "tags": tags, "mode": "relationship"}

        # =========================
        # 5) Objects: possession, gone, location, ambiguity
        # =========================
        place = self._extract_place(text_l)
        label = self._extract_object(text_l)
        colour = self._extract_colour(text_l)

        # "<name> has the (red) ball"
        poss = re.match(r"^\s*([a-z]+)\s+has\s+(the\s+)?(?:(red|blue|orange|green|yellow)\s+)?(swing|ball|toy|stick|box)\b", text_l)
        if poss:
            holder_name = poss.group(1).strip().title()
            holder = self.bridge.find_entity(holder_name) or self.bridge.confirm_entity(holder_name, "person", confidence=0.5, origin="event")
            lab = poss.group(4)
            col = poss.group(3)

            obj = self.objects.find(lab, colour=col, include_gone=True) or self.objects.create(lab, colour=col, owner_entity_id=speaker.entity_id)
            self.objects.attach(obj, holder.entity_id)
            self.objects.set_location(obj, place)

            return {"answer": f"Noted. {holder_name} has the {(col + ' ') if col else ''}{lab}.", "tags": tags, "mode": "object"}

        # standard object mention
        if label:
            # gone
            if any(w in text_l for w in ["gone", "bin", "threw", "thrown away", "lost"]):
                obj = self.objects.find(label, colour=colour, include_gone=True) or self.objects.create(label, colour=colour, owner_entity_id=speaker.entity_id)
                self.objects.set_location(obj, place)
                self.objects.mark_gone(obj)
                return {"answer": f"Okay — the {(colour + ' ') if colour else ''}{label} is gone (but remembered).", "tags": tags, "mode": "object"}

            # colour specified -> direct
            if colour:
                obj = self.objects.find(label, colour=colour, include_gone=True) or self.objects.create(label, colour=colour, owner_entity_id=speaker.entity_id)
                self.objects.set_location(obj, place)
                return {"answer": f"Noted. {colour} {label}.", "tags": tags, "mode": "object"}

            # no colour -> ambiguity check
            existing = self.objects.candidates(label, include_gone=False)
            if len(existing) == 1 and existing[0].colour:
                self.awaiting = {"type": "obj_disambiguate", "label": label, "candidate_id": existing[0].object_id}
                return {"answer": f"Do you mean the {existing[0].colour} {label}? (yes/no)", "tags": tags, "mode": "object"}

            if len(existing) > 1:
                self.awaiting = {"type": "obj_colour", "label": label}
                return {"answer": "Which one is it? (say a colour like: orange)", "tags": tags, "mode": "object"}

            # create unknown
            obj = self.objects.create(label, colour=None, owner_entity_id=speaker.entity_id)
            self.objects.set_location(obj, place)
            return {"answer": f"Noted. {label}.", "tags": tags, "mode": "object"}

        # =========================
        # 6) Experience gating: place-first, only if place+object in sentence
        # =========================
        if place and self._extract_object(text_l):
            obj = self._extract_object(text_l)
            place_known = self.experiences.has_place(place)
            pair_known = self.experiences.has_place_object(place, obj)

            if not place_known:
                self.awaiting = {"type": "confirm_place", "place": place, "object": obj}
                return {"answer": f"Is this a {place} I already know? (yes/no)", "tags": tags, "mode": "experience"}

            if place_known and not pair_known:
                exp = self.experiences.create(place, obj)
                self.awaiting = self._experience_questions(exp)
                return {"answer": f"I know the {place}. Let's learn about the {obj} here. {self.awaiting['question']}", "tags": tags, "mode": "experience"}

        # =========================
        # 7) Soft person promotion in events (optional)
        # =========================
        for tok in re.findall(r"\b[A-Z][a-z]+\b", text):
            if tok.lower() in {"i", "we", "the", "a", "an"}:
                continue
            if not self.bridge.find_entity(tok):
                self.bridge.confirm_entity(tok, "person", confidence=0.4, origin="event")

        # =========================
        # 8) Event capture LAST (sensory aware)
        # =========================
        if place or ("sensory" in tags):
            sx = self.sensory.extract(text)
            self.events.create_event(
                participants={speaker.entity_id},
                place=place,
                description=text,
                timestamp=now,
                smells=sx.smells,
                sounds=sx.sounds,
            )
            return {"answer": "Noted — remembered.", "tags": tags, "mode": "event"}

        return {"answer": "Noted.", "tags": tags, "mode": "default"}
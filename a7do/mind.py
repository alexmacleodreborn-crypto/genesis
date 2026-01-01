import re
import time
from a7do.entity_promotion import EntityPromotionBridge
from a7do.objects import ObjectManager
from a7do.relationships import RelationshipStore
from a7do.event_graph import EventGraph
from a7do.sensory import SensoryParser
from a7do.language import LanguageModule
from a7do.recall import RecallEngine
from a7do.memory import Memory
from a7do.tagger import Tagger


class A7DOMind:
    def __init__(self):
        self.bridge = EntityPromotionBridge()
        self.objects = ObjectManager()
        self.relationships = RelationshipStore()
        self.events = EventGraph()
        self.sensory = SensoryParser()
        self.language = LanguageModule()
        self.recall_engine = RecallEngine(self.events, self.bridge.entities)
        self.memory = Memory()
        self.tagger = Tagger()
        self.awaiting = None

        self.agent = self.bridge.confirm_entity("A7DO", "agent", confidence=1.0)

    def speaker(self):
        name = self.language.speaker() or "Alex Macleod"
        return self.bridge.confirm_entity(name, "person", confidence=1.0)

    def process(self, text):
        self.memory.add(text=text, ts=time.time())
        text_l = text.lower()
        speaker = self.speaker()

        # identity
        if text_l.startswith("my name is"):
            name = text.split("my name is")[-1].strip()
            self.language.lock_speaker(name)
            self.bridge.confirm_entity(name, "person", confidence=1.0)
            return {"answer": f"Noted. You are {name}."}

        # pets
        if "is my dog" in text_l:
            name = text.split("is my dog")[0].strip()
            dog = self.bridge.confirm_entity(name, "pet", confidence=1.0)
            self.relationships.add(speaker.entity_id, dog.entity_id, "pet")
            return {"answer": f"{name} is your dog."}

        # kinship
        if "is your uncle" in text_l:
            name = text.split("is your uncle")[0].strip()
            person = self.bridge.confirm_entity(name, "person", confidence=1.0)
            self.relationships.add(self.agent.entity_id, person.entity_id, "uncle")
            return {"answer": f"{name} is my uncle."}

        if "is my uncle" in text_l:
            name = text.split("is my uncle")[0].strip()
            person = self.bridge.confirm_entity(name, "person", confidence=1.0)
            self.relationships.add(speaker.entity_id, person.entity_id, "uncle")
            return {"answer": f"{name} is your uncle."}

        # objects
        if "ball" in text_l:
            colour = None
            for c in ["red", "blue", "orange"]:
                if c in text_l:
                    colour = c
            obj = self.objects.find("ball", colour)
            if not obj:
                obj = self.objects.create("ball", colour, speaker.entity_id)
            return {"answer": f"Noted. {colour or ''} ball."}

        # gone
        if "gone" in text_l:
            for obj in self.objects.objects.values():
                if obj.label in text_l:
                    self.objects.mark_gone(obj)
                    return {"answer": f"The {obj.label} is gone."}

        # event LAST
        place = None
        for p in ["park", "home"]:
            if p in text_l:
                place = p

        if place:
            self.events.create_event(
                participants={speaker.entity_id},
                place=place,
                description=text,
                timestamp=time.time(),
            )
            return {"answer": "Noted — remembered."}

        return {"answer": "Noted."}
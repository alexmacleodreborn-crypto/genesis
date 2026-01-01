import re

EMOTIONS = ["happy", "sad", "excited", "angry", "calm", "scared", "nervous"]
PLACES = ["park", "home", "garden", "vet", "beach", "gate", "street"]
OBJECTS = ["swing", "ball", "toy", "stick", "box"]

class Tagger:
    def tag(self, text: str):
        t = (text or "").lower()
        tags = set()

        if any(w in t for w in EMOTIONS):
            tags.add("emotion")

        if any(re.search(rf"\b{o}\b", t) for o in OBJECTS):
            tags.add("object")

        if any(w in t for w in PLACES):
            tags.add("place")

        if "dog" in t or "pet" in t:
            tags.add("pet")

        if "smell" in t or "hear" in t or "sound" in t:
            tags.add("sensory")

        return sorted(tags)
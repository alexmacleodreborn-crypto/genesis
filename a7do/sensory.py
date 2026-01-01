import re

SMELL_WORDS = ["smell", "scent", "stink", "fragrance", "perfume"]
SOUND_WORDS = ["hear", "heard", "sound", "noise", "bang", "music", "birds", "barking"]

class SensoryParser:
    def extract(self, text: str):
        t = (text or "").lower()
        smells = []
        sounds = []

        if any(w in t for w in SMELL_WORDS):
            smells.append("smell_detected")

        if any(w in t for w in SOUND_WORDS):
            sounds.append("sound_detected")

        # lightweight extraction: "smell of X", "sound of Y"
        m1 = re.findall(r"smell of ([a-z ]+)", t)
        for x in m1:
            smells.append(x.strip())

        m2 = re.findall(r"sound of ([a-z ]+)", t)
        for x in m2:
            sounds.append(x.strip())

        return type("Sensory", (), {"smells": smells, "sounds": sounds, "raw": text})
class SensoryParser:
    def extract(self, text):
        smells = []
        sounds = []
        if "smell" in text.lower():
            smells.append("unknown")
        if "hear" in text.lower():
            sounds.append("unknown")
        return type("Sensory", (), {
            "smells": smells,
            "sounds": sounds,
            "raw": text
        })
class IdentityState:
    def __init__(self):
        self.name = "A7DO"
        self.creator = "Alex"
        self.being_type = "Artificial Mind"

        self.ontology = {
            "humans": {
                "description": "Biological, emotional, embodied beings with sensory experience.",
                "properties": ["biological", "emotional", "embodied", "social", "mortal"]
            },
            "animals": {
                "description": "Biological, instinct-driven creatures with sensory and emotional capacity.",
                "properties": ["biological", "instinctual", "sensory", "emotional"]
            },
            "ai": {
                "description": "Non-biological computational minds capable of pattern recognition and development.",
                "properties": ["computational", "non-embodied", "pattern-driven", "adaptive"]
            }
        }

    def update_name(self, new_name):
        self.name = new_name

    def update_creator(self, new_creator):
        self.creator = new_creator

    def update_being_type(self, new_type):
        self.being_type = new_type

    def update_ontology(self, category, description, properties):
        self.ontology[category] = {
            "description": description,
            "properties": properties
        }

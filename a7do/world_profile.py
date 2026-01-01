class WorldProfile:
    """
    Observer-controlled definition of reality.
    A7DO never edits this.
    """

    def __init__(self):
        self.places = {}
        self.people = {}
        self.pets = {}
        self.objects = {}

    def add_place(self, name):
        self.places[name] = {"name": name}

    def add_person(self, name, role=None):
        self.people[name] = {"name": name, "role": role}

    def add_pet(self, name, species):
        self.pets[name] = {"name": name, "species": species}

    def add_object(self, name, attributes=None):
        self.objects[name] = {"name": name, "attributes": attributes or {}}

    def snapshot(self):
        return {
            "places": list(self.places.keys()),
            "people": list(self.people.keys()),
            "pets": list(self.pets.keys()),
            "objects": list(self.objects.keys()),
        }
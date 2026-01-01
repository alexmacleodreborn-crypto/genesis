class RecallEngine:
    def __init__(self, events, entities, objects, relationships, experiences):
        self.events = events
        self.entities = entities
        self.objects = objects
        self.relationships = relationships
        self.experiences = experiences

    def entity_name(self, entity_id):
        e = self.entities.get(entity_id)
        return e.name if e else "—"

    # ---------- object recall ----------
    def where_is_object(self, label, colour=None):
        obj = self.objects.find(label, colour=colour, include_gone=True)
        if not obj:
            c = f"{colour} " if colour else ""
            return f"I don't know that {c}{label} yet."
        c = f"{obj.colour} " if obj.colour else ""
        if obj.state == "gone":
            return f"The {c}{label} is gone (but remembered). Last place: {obj.location or 'unknown'}."
        return f"Last known place for the {c}{label}: {obj.location or 'unknown'}."

    def what_objects_do_i_have(self, owner_entity_id, label=None):
        objs = self.objects.list_owned(owner_entity_id, label=label, include_gone=True)
        if not objs:
            return "None."
        lines = []
        for o in objs:
            c = f"{o.colour} " if o.colour else ""
            lines.append(f"- {c}{o.label} | state={o.state} | last_place={o.location or 'unknown'}")
        return "\n".join(lines)

    def do_i_have_object(self, owner_entity_id, label, colour=None):
        objs = self.objects.list_owned(owner_entity_id, label=label, include_gone=True)
        if colour:
            objs = [o for o in objs if o.colour == colour]
        if not objs:
            return "No."
        if any(o.state != "gone" for o in objs):
            return "Yes."
        return "You used to, but it is marked as gone."

    def what_does_entity_have(self, entity_id):
        objs = self.objects.list_attached_to(entity_id, include_gone=True)
        if not objs:
            return "None."
        lines = []
        for o in objs:
            c = f"{o.colour} " if o.colour else ""
            lines.append(f"- {c}{o.label} | state={o.state} | last_place={o.location or 'unknown'}")
        return "\n".join(lines)

    # ---------- experience recall ----------
    def experiences_at_place(self, place: str):
        exps = [e for e in self.experiences.experiences.values() if e.place == place]
        if not exps:
            return "None."
        out = []
        for e in exps:
            out.append(f"- {e.object_label}: liked={e.preference or '—'} felt={e.emotion or '—'}")
        return "\n".join(out)
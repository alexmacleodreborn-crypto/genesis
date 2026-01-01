def build_brain_dot(mind) -> str:
    """
    Graphviz DOT graph (works on Streamlit Cloud via st.graphviz_chart)
    Nodes: entities, objects, places, experiences
    Edges: relationships, owns, attached_to, experienced_at
    """
    def esc(s: str) -> str:
        return (s or "").replace('"', "'")

    lines = []
    lines.append('digraph A7DO {')
    lines.append('rankdir=LR;')
    lines.append('bgcolor="transparent";')
    lines.append('node [shape=ellipse, style="filled", fillcolor="white"];')

    # clusters
    lines.append('subgraph cluster_entities { label="Entities"; style="rounded";')
    for e in mind.bridge.entities.values():
        nid = f'ent_{e.entity_id[:8]}'
        label = f'{esc(e.name)}\\n({e.kind})\\nconf={e.confidence:.2f}'
        lines.append(f'"{nid}" [shape=oval, fillcolor="lightblue", label="{label}"];')
    lines.append('}')

    lines.append('subgraph cluster_objects { label="Objects"; style="rounded";')
    for o in mind.objects.objects.values():
        nid = f'obj_{o.object_id[:8]}'
        label = f'{esc((o.colour+" ") if o.colour else "")}{esc(o.label)}\\nstate={o.state}'
        lines.append(f'"{nid}" [shape=box, fillcolor="lightgoldenrod", label="{label}"];')
    lines.append('}')

    # places as nodes (from events + experiences + object locations)
    places = set()
    for ev in mind.events.events:
        if ev.place:
            places.add(ev.place)
    for o in mind.objects.objects.values():
        if o.location:
            places.add(o.location)
    for ex in mind.experiences.experiences.values():
        if ex.place:
            places.add(ex.place)

    lines.append('subgraph cluster_places { label="Places"; style="rounded";')
    for p in sorted(places):
        lines.append(f'"place_{esc(p)}" [shape=diamond, fillcolor="palegreen", label="{esc(p)}"];')
    lines.append('}')

    # experiences
    lines.append('subgraph cluster_experiences { label="Experiences"; style="rounded";')
    for ex in mind.experiences.experiences.values():
        nid = f'exp_{esc(ex.experience_id)}'
        label = f'{esc(ex.object_label)} @ {esc(ex.place)}'
        lines.append(f'"{nid}" [shape=note, fillcolor="lavender", label="{label}"];')
    lines.append('}')

    # edges: relationships
    for r in mind.relationships.relations:
        a = mind.bridge.entities.get(r.subject_id)
        b = mind.bridge.entities.get(r.object_id)
        if not a or not b:
            continue
        na = f'ent_{a.entity_id[:8]}'
        nb = f'ent_{b.entity_id[:8]}'
        lines.append(f'"{na}" -> "{nb}" [label="{esc(r.rel_type)}", color="gray40"];')

    # edges: ownership + attachment + location
    for o in mind.objects.objects.values():
        no = f'obj_{o.object_id[:8]}'
        if o.owner_entity_id and o.owner_entity_id in mind.bridge.entities:
            e = mind.bridge.entities[o.owner_entity_id]
            ne = f'ent_{e.entity_id[:8]}'
            lines.append(f'"{ne}" -> "{no}" [label="owns", color="goldenrod4"];')
        if o.attached_to and o.attached_to in mind.bridge.entities:
            e = mind.bridge.entities[o.attached_to]
            ne = f'ent_{e.entity_id[:8]}'
            lines.append(f'"{ne}" -> "{no}" [label="has", color="sienna4"];')
        if o.location:
            lines.append(f'"{no}" -> "place_{esc(o.location)}" [label="last_place", color="darkgreen"];')

    # edges: experiences link to place
    for ex in mind.experiences.experiences.values():
        nx = f'exp_{esc(ex.experience_id)}'
        lines.append(f'"{nx}" -> "place_{esc(ex.place)}" [label="at", color="purple"];')

    lines.append('}')
    return "\n".join(lines)
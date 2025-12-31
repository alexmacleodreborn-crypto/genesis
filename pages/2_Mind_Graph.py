import streamlit as st
import networkx as nx
from pyvis.network import Network
import tempfile
import os

from a7do.mind import A7DOMind

st.set_page_config(page_title="A7DO Mind Graph", layout="wide")
st.title("🕸️ A7DO — Mind Graph")

mind: A7DOMind = st.session_state.get("mind")
if not mind:
    st.warning("Mind not initialised yet.")
    st.stop()

G = nx.Graph()

# ---- Nodes: entities ----
for e in mind.bridge.entities.values():
    label = f"{e.name}\n({e.kind})"
    G.add_node(
        e.entity_id,
        label=label,
        title=f"Entity: {e.name}\nKind: {e.kind}\nOwner: {e.owner_name or '—'}",
        shape="ellipse",
    )

# ---- Edges: first-class relationships ----
for r in mind.relationships.all():
    if r.subject_id in mind.bridge.entities and r.object_id in mind.bridge.entities:
        G.add_edge(r.subject_id, r.object_id, label=r.rel_type)

# ---- Fallback: old owner_name edges (only if no relationship exists) ----
# (keeps backwards compatibility if you have older stored entities)
existing_pairs = {(r.subject_id, r.object_id, r.rel_type) for r in mind.relationships.all()}
for e in mind.bridge.entities.values():
    if e.owner_name:
        owner = mind.bridge.find_entity(e.owner_name, owner_name=None)
        if owner:
            if (owner.entity_id, e.entity_id, "pet") not in existing_pairs and (owner.entity_id, e.entity_id, "owns") not in existing_pairs:
                G.add_edge(owner.entity_id, e.entity_id, label="owns")

# ---- Event nodes + edges ----
for ev in mind.events_graph.events.values():
    ev_id = f"event-{ev.event_id}"
    G.add_node(
        ev_id,
        label=ev.place or "Event",
        title=ev.description,
        shape="box",
    )
    for pid in ev.participants:
        if pid in mind.bridge.entities:
            G.add_edge(pid, ev_id, label="experienced")

# ---- Render ----
net = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="black")
net.from_nx(G)
net.toggle_physics(True)

with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
    net.save_graph(tmp.name)
    html_path = tmp.name

with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

st.components.v1.html(html, height=800, scrolling=True)
os.unlink(html_path)
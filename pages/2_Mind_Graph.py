import streamlit as st
import networkx as nx
from pyvis.network import Network
import tempfile
import os

from a7do.mind import A7DOMind

st.set_page_config(page_title="A7DO Mind Graph", layout="wide")

st.title("🧠 A7DO — Mind Graph")

mind: A7DOMind = st.session_state.get("mind")

if not mind:
    st.warning("Mind not initialised yet.")
    st.stop()

G = nx.Graph()

# ---- Add entity nodes ----
for e in mind.bridge.entities.values():
    label = f"{e.name}\n({e.kind})"
    G.add_node(
        e.entity_id,
        label=label,
        title=f"Entity: {e.name}\nKind: {e.kind}\nOwner: {e.owner_name}",
        color="lightblue" if e.kind == "person" else "lightgreen",
        shape="ellipse",
    )

# ---- Ownership edges ----
for e in mind.bridge.entities.values():
    if e.owner_name:
        owner = mind.bridge.find_entity(e.owner_name)
        if owner:
            G.add_edge(
                owner.entity_id,
                e.entity_id,
                label="owns",
                color="gray",
            )

# ---- Event nodes + edges ----
for ev in mind.events_graph.events.values():
    ev_id = f"event-{ev.event_id}"
    G.add_node(
        ev_id,
        label=ev.place or "Event",
        title=ev.description,
        color="orange",
        shape="box",
    )
    for pid in ev.participants:
        if pid in mind.bridge.entities:
            G.add_edge(pid, ev_id, label="experienced", color="orange")

# ---- Render with PyVis ----
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
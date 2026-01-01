import streamlit as st
import networkx as nx
from pyvis.network import Network
import tempfile
import os

from a7do.mind import A7DOMind

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(page_title="A7DO Mind Graph", layout="wide")
st.title("🕸️ A7DO — Mind Graph")

# -------------------------------------------------
# Get persistent mind
# -------------------------------------------------
mind: A7DOMind = st.session_state.get("mind")

if not mind:
    st.warning("Mind not initialised yet.")
    st.stop()

# -------------------------------------------------
# Helper: safe getters
# -------------------------------------------------
def safe_entities():
    bridge = getattr(mind, "bridge", None)
    if not bridge:
        return []
    return list(getattr(bridge, "entities", {}).values())

def safe_relationships():
    store = getattr(mind, "relationships", None)
    if not store:
        return []
    try:
        return store.all()
    except Exception:
        return []

def safe_pending():
    store = getattr(mind, "pending_relationships", None)
    if not store:
        return []
    try:
        return store.list_pending()
    except Exception:
        return []

def safe_events():
    eg = getattr(mind, "events_graph", None)
    if not eg:
        return []
    return list(getattr(eg, "events", {}).values())

# -------------------------------------------------
# Build graph
# -------------------------------------------------
G = nx.Graph()

# -------------------------------------------------
# Add entity nodes
# -------------------------------------------------
for e in safe_entities():
    label = f"{e.name}\n({e.kind})"
    title = f"Entity: {e.name}\nKind: {e.kind}"
    if getattr(e, "owner_name", None):
        title += f"\nOwner: {e.owner_name}"

    G.add_node(
        e.entity_id,
        label=label,
        title=title,
        shape="ellipse",
    )

# -------------------------------------------------
# Add confirmed relationship edges
# -------------------------------------------------
for r in safe_relationships():
    if r.subject_id in G.nodes and r.object_id in G.nodes:
        G.add_edge(
            r.subject_id,
            r.object_id,
            label=r.rel_type,
            color="black",
            width=2,
        )

# -------------------------------------------------
# Add pending relationship edges (dashed red)
# -------------------------------------------------
for p in safe_pending():
    if p.subject_id in G.nodes and p.object_id in G.nodes:
        G.add_edge(
            p.subject_id,
            p.object_id,
            label=f"{p.rel_type}? ({p.confidence:.2f})",
            color="red",
            dashes=True,
            width=2,
        )

# -------------------------------------------------
# Add event nodes + edges
# -------------------------------------------------
for ev in safe_events():
    ev_node_id = f"event-{ev.event_id}"

    G.add_node(
        ev_node_id,
        label=ev.place or "Event",
        title=ev.description,
        shape="box",
        color="#EEEEEE",
    )

    for pid in ev.participants:
        if pid in G.nodes:
            G.add_edge(
                pid,
                ev_node_id,
                label="experienced",
                color="#888888",
                width=1,
            )

# -------------------------------------------------
# Render with PyVis
# -------------------------------------------------
net = Network(
    height="800px",
    width="100%",
    bgcolor="#ffffff",
    font_color="black",
)

net.from_nx(G)

# Patch pending edges (pyvis sometimes drops dash styling)
for e in net.edges:
    if isinstance(e.get("label"), str) and "?" in e["label"]:
        e["color"] = "red"
        e["dashes"] = True

net.toggle_physics(True)

# -------------------------------------------------
# Display
# -------------------------------------------------
with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
    net.save_graph(tmp.name)
    html_path = tmp.name

with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

st.components.v1.html(html, height=850, scrolling=True)
os.unlink(html_path)

# -------------------------------------------------
# Legend
# -------------------------------------------------
st.markdown(
    """
### Legend
- **Black edge** → confirmed relationship  
- **Red dashed edge** → inferred (pending) relationship  
- **Box node** → shared event  
"""
)
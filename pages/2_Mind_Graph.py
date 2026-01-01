import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

st.set_page_config(page_title="A7DO Mind Graph", layout="wide")

st.title("🧠 A7DO Mind Graph")

mind = st.session_state.get("mind")

if not mind:
    st.info("Mind not initialised yet.")
    st.stop()


# -------------------------
# Safe accessors
# -------------------------

def safe_events():
    """
    Returns a list of Event objects regardless of internal storage shape.
    """
    evs = getattr(mind.events, "events", [])

    # If someone accidentally passes a dict, recover
    if isinstance(evs, dict):
        return list(evs.values())

    # Normal case (list)
    if isinstance(evs, list):
        return evs

    return []


def safe_entities():
    return getattr(mind.bridge, "entities", {})


def safe_relationships():
    return getattr(mind.bridge, "relationships", [])


# -------------------------
# Build Graph
# -------------------------

G = nx.Graph()

# --- Entities ---
entities = safe_entities()
for eid, ent in entities.items():
    label = f"{ent.name}\n({ent.kind})"
    G.add_node(eid, label=label, type=ent.kind)


# --- Relationships ---
for rel in safe_relationships():
    G.add_edge(
        rel.source,
        rel.target,
        label=rel.relation
    )


# --- Events ---
for ev in safe_events():
    ev_id = f"event:{ev.id}"
    G.add_node(ev_id, label="Event", type="event")

    for ent_id in ev.entities:
        if ent_id in G:
            G.add_edge(ent_id, ev_id, label="experienced")

    for obj_id in ev.objects:
        if obj_id in G:
            G.add_edge(obj_id, ev_id, label="involved")


# -------------------------
# Draw Graph
# -------------------------

if len(G.nodes) == 0:
    st.info("No entities or events to display yet.")
    st.stop()

pos = nx.spring_layout(G, seed=42, k=1.1)

plt.figure(figsize=(14, 14))

node_colors = []
for _, data in G.nodes(data=True):
    t = data.get("type", "")
    if t == "person":
        node_colors.append("#7dafff")
    elif t == "pet":
        node_colors.append("#9aff7d")
    elif t == "object":
        node_colors.append("#ffd27d")
    elif t == "place":
        node_colors.append("#ff9a9a")
    elif t == "event":
        node_colors.append("#cccccc")
    else:
        node_colors.append("#dddddd")

nx.draw(
    G,
    pos,
    with_labels=False,
    node_size=2000,
    node_color=node_colors,
    edgecolors="black"
)

labels = nx.get_node_attributes(G, "label")
nx.draw_networkx_labels(G, pos, labels, font_size=9)

edge_labels = nx.get_edge_attributes(G, "label")
nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=8)

st.pyplot(plt)
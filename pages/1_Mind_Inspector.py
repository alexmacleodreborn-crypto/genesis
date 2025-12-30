import streamlit as st

st.set_page_config(layout="wide")
st.title("🧠 Mind Inspector")

mind = st.session_state.get("mind")

if not mind:
    st.error("Mind not initialised.")
    st.stop()

# --------------------------------------------------
# Cognitive log (process flow)
# --------------------------------------------------

st.subheader("🧠 Cognitive Activity Log")

if hasattr(mind, "log") and mind.log:
    for entry in mind.log:
        st.code(entry)
else:
    st.caption("No cognitive log entries yet.")

# --------------------------------------------------
# Event Frames (Flow Memory)
# --------------------------------------------------

st.subheader("🧩 Event Frames (Lived Experience)")

event_memory = mind.events

if not event_memory.frames:
    st.caption("No events recorded yet.")
else:
    for evt in event_memory.frames[-10:]:
        with st.expander(f"Event {evt.event_id}  ·  {round(evt.t1 - evt.t0, 2)}s"):
            st.json(evt.snapshot())

# --------------------------------------------------
# Event Silos (Life-streams)
# --------------------------------------------------

st.subheader("🧬 Entity Life-Streams (Silos)")

if not event_memory.silos:
    st.caption("No silos yet.")
else:
    for entity_id, event_ids in event_memory.silos.items():
        with st.expander(f"Entity {entity_id}"):
            st.write("Event IDs:")
            st.write(event_ids)

# --------------------------------------------------
# Reoccurrence
# --------------------------------------------------

st.subheader("🔁 Reoccurrence Signals")

st.json(mind.reoccurrence.summary())

# --------------------------------------------------
# Entity Graph
# --------------------------------------------------

st.subheader("🧩 Entity Graph")
st.json(mind.entities.summary())

# --------------------------------------------------
# Fact Ledger
# --------------------------------------------------

st.subheader("✅ Entity Facts")
st.json(mind.facts.summary())

# --------------------------------------------------
# Unbound labels (names waiting for context)
# --------------------------------------------------

st.subheader("🏷 Unbound Labels")
st.json(mind.unbound_names)
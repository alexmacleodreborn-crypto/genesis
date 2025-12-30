import streamlit as st

st.set_page_config(layout="wide")
st.title("🧠 Mind Inspector")

mind = st.session_state.get("mind")
if not mind:
    st.error("Mind not initialised.")
    st.stop()

st.subheader("🧠 Cognitive Activity Log")
if getattr(mind, "log", None):
    for entry in mind.log:
        st.code(entry)
else:
    st.caption("No cognitive log entries yet.")

st.subheader("🧩 Event Frames (Flow Memory)")
event_memory = mind.events
if not event_memory.frames:
    st.caption("No events recorded yet.")
else:
    for evt in event_memory.frames[-10:]:
        with st.expander(f"{evt.event_id} · {round(evt.t1 - evt.t0, 2)}s"):
            st.json(evt.snapshot())

st.subheader("🧬 Entity Life-Streams (Silos)")
if not event_memory.silos:
    st.caption("No silos yet.")
else:
    for entity_id, event_ids in event_memory.silos.items():
        with st.expander(f"Entity {entity_id}"):
            st.write(event_ids)

st.subheader("🔁 Reoccurrence")
st.json(mind.reoccurrence.summary())

st.subheader("🧩 Entity Graph")
st.json(mind.entities.summary())

st.subheader("✅ Fact Ledger")
st.json(mind.facts.summary())

st.subheader("🏷 Unbound Proper Nouns")
st.json(mind.unbound_names)

st.subheader("🧠 Linguistic Role Guard (LRG) Quick Test")
test_text = st.text_input("Type a sentence to inspect roles", "My dog is called Xena and I feel excited at the park")
roles = mind.lrg.classify(test_text)
st.json([{"text": r.text, "role": r.role} for r in roles])
st.write("Naming context:", mind.lrg.is_naming_context(test_text))
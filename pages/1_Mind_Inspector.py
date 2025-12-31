import streamlit as st
from a7do.mind import A7DOMind

st.set_page_config(page_title="A7DO – Mind Inspector", layout="wide")
st.title("🧠 A7DO Mind Inspector")

if "mind" not in st.session_state:
    st.session_state.mind = A7DOMind()

mind = st.session_state.mind

# ------------------------------
# Memory Stream
# ------------------------------
st.subheader("📜 Event / Memory Stream")
events = mind.events.recent(20) if hasattr(mind.events, "recent") else []

for i, e in enumerate(events[::-1], 1):
    with st.expander(f"Event {i}"):
        st.json(e if isinstance(e, dict) else {"event": str(e)})

# ------------------------------
# Pending Entities
# ------------------------------
st.subheader("🧩 Pending Entities")

pending = mind.bridge.pending

if not pending:
    st.caption("No pending entities.")
else:
    for name, p in pending.items():
        with st.expander(f"{p.name} (confidence {p.confidence:.2f})"):
            kind = st.selectbox(
                "Confirm as",
                ["person", "pet", "place", "concept"],
                key=f"kind_{name}",
            )

            is_self = st.checkbox("This is me", key=f"self_{name}")
            is_creator = st.checkbox("This is my creator", key=f"creator_{name}")

            if st.button("Confirm", key=f"confirm_{name}"):
                mind.bridge.confirm_entity(
                    name=p.name,
                    kind=kind,
                    is_self=is_self,
                    is_creator=is_creator,
                )
                st.experimental_rerun()

# ------------------------------
# Entity Graph
# ------------------------------
st.subheader("🗂️ Entity Graph")

if not mind.bridge.entities:
    st.caption("No promoted entities yet.")
else:
    for e in mind.bridge.entities.values():
        st.markdown(
            f"""
**{e.name}**  
Type: `{e.kind}`  
Aliases: {", ".join(e.aliases) if e.aliases else "—"}
"""
        )

# ------------------------------
# System Signal
# ------------------------------
st.subheader("📡 System Signal")
if mind._last_signal:
    st.json(mind._last_signal)
else:
    st.caption("No system signals.")
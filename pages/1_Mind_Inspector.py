import streamlit as st
from a7do.mind import A7DOMind

st.set_page_config(page_title="A7DO – Mind Inspector", layout="wide")
st.title("🧠 A7DO Mind Inspector")

if "mind" not in st.session_state:
    st.session_state.mind = A7DOMind()

mind = st.session_state.mind

# ------------------------------
# Memory
# ------------------------------
st.subheader("📜 Event / Memory Stream")

frames = mind.events.recent(20) if hasattr(mind.events, "recent") else []
if not frames:
    st.caption("No events yet.")
else:
    for i, f in enumerate(frames[::-1], 1):
        with st.expander(f"Event {i}"):
            st.json(f if isinstance(f, dict) else {"event": str(f)})

# ------------------------------
# Pending Entities
# ------------------------------
st.subheader("🧩 Pending Entities")

PRONOUNS = {"i", "me", "my", "mine", "you", "your"}

if not mind.bridge.pending:
    st.caption("No pending entities.")
else:
    for key, p in list(mind.bridge.pending.items()):
        with st.expander(f"{p.name} (confidence {p.confidence:.2f})"):
            if p.name.lower() in PRONOUNS:
                st.info("This is a pronoun — it will be handled as language, not an entity.")
                if st.button("Record as language rule", key=f"lang_{key}"):
                    del mind.bridge.pending[key]
                    st.rerun()
                continue

            kind = st.selectbox(
                "Confirm as",
                ["person", "pet", "place", "object", "concept"],
                key=f"kind_{key}",
            )

            if st.button("Confirm entity", key=f"confirm_{key}"):
                mind.bridge.confirm_entity(
                    name=p.name,
                    kind=kind,
                    owner_name=getattr(mind.identity, "creator", None),
                )
                st.rerun()

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
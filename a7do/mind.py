import streamlit as st
from a7do.mind import A7DOMind

st.set_page_config(page_title="A7DO – Mind Inspector", layout="wide")
st.title("🧠 A7DO Mind Inspector")

# ------------------------------
# Session
# ------------------------------
if "mind" not in st.session_state:
    st.session_state.mind = A7DOMind()

mind = st.session_state.mind

# ------------------------------
# Memory Stream
# ------------------------------
st.subheader("📜 Event / Memory Stream")

frames = []
if hasattr(mind.events, "recent"):
    frames = mind.events.recent(20)

if not frames:
    st.caption("No events yet.")
else:
    for i, frame in enumerate(frames[::-1], 1):
        with st.expander(f"Event {i}"):
            st.json(frame if isinstance(frame, dict) else {"event": str(frame)})

# ------------------------------
# Pending Entities
# ------------------------------
st.subheader("🧩 Pending Entities")

PRONOUNS = {"i", "me", "my", "mine", "you", "your"}

pending = mind.bridge.pending

if not pending:
    st.caption("No pending entities.")
else:
    for key, p in pending.items():
        with st.expander(f"{p.name} (confidence {p.confidence:.2f})"):
            lname = p.name.lower()

            # ---- Pronoun handling (language, not entity)
            if lname in PRONOUNS:
                st.info(
                    f"'{p.name}' is a **pronoun**, not an entity.\n\n"
                    "This will be handled as **language knowledge** "
                    "and mapped to the current speaker or listener."
                )

                if st.button("Record as language rule", key=f"lang_{key}"):
                    # For now we just remove from pending
                    del mind.bridge.pending[key]
                    st.success(f"Recorded '{p.name}' as language knowledge.")
                    st.rerun()

                continue

            # ---- Normal entity confirmation
            kind = st.selectbox(
                "Confirm as",
                ["person", "pet", "place", "object", "concept"],
                key=f"kind_{key}",
            )

            is_self = st.checkbox("This is me", key=f"self_{key}")
            is_creator = st.checkbox("This is my creator", key=f"creator_{key}")

            if st.button("Confirm entity", key=f"confirm_{key}"):
                mind.bridge.confirm_entity(
                    name=p.name,
                    kind=kind,
                    owner_name=getattr(mind.identity, "creator", None),
                    is_self=is_self,
                    is_creator=is_creator,
                )
                st.success(f"Confirmed {p.name} as {kind}.")
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
Anchors:  
- Places: {", ".join(e.places) if e.places else "—"}  
- Relations: {", ".join(e.relations) if e.relations else "—"}  
- Activities: {", ".join(e.activities) if e.activities else "—"}
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
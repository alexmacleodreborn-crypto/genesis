import streamlit as st
from a7do.mind import A7DOMind

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="A7DO Cognitive Interface",
    page_icon="🧠",
    layout="wide",
)

# -------------------------------------------------
# Persistent Mind (shared across pages)
# -------------------------------------------------
if "mind" not in st.session_state:
    st.session_state.mind = A7DOMind()

mind: A7DOMind = st.session_state.mind

# -------------------------------------------------
# Sidebar — Identity & Navigation
# -------------------------------------------------
st.sidebar.title("🧠 A7DO")

identity = mind.identity

st.sidebar.markdown("### Identity")
st.sidebar.markdown(f"**Name:** {getattr(identity, 'creator', '—') or '—'}")
st.sidebar.markdown("**Type:** Artificial Cognitive System")

st.sidebar.divider()

st.sidebar.markdown("### Navigation")
st.sidebar.markdown(
    """
- 💬 **Chat** (this page)  
- 🕸️ **Mind Graph** → use left menu  
"""
)

st.sidebar.divider()

# -------------------------------------------------
# Main Chat Interface
# -------------------------------------------------
st.title("💬 A7DO — Cognitive Dialogue")

st.caption(
    "This interface lets you speak naturally while A7DO builds entities, "
    "relationships, and shared experiences in real time."
)

# -------------------------------------------------
# Chat history (simple, safe)
# -------------------------------------------------
if "chat_log" not in st.session_state:
    st.session_state.chat_log = []

for role, msg in st.session_state.chat_log:
    with st.chat_message(role):
        st.markdown(msg)

# -------------------------------------------------
# User input
# -------------------------------------------------
user_text = st.chat_input("Say something…")

if user_text:
    # Show user message
    st.session_state.chat_log.append(("user", user_text))
    with st.chat_message("user"):
        st.markdown(user_text)

    # Process through the mind
    result = mind.process(user_text)

    answer = result.get("answer", "…")

    # Show A7DO response
    st.session_state.chat_log.append(("assistant", answer))
    with st.chat_message("assistant"):
        st.markdown(answer)

# -------------------------------------------------
# Debug / Introspection Panel
# -------------------------------------------------
with st.expander("🔍 Mind Inspector", expanded=False):

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### Entities")
        if mind.bridge.entities:
            for e in mind.bridge.entities.values():
                st.markdown(
                    f"- **{e.name}** ({e.kind})"
                    + (f" — owner: {e.owner_name}" if e.owner_name else "")
                )
        else:
            st.markdown("_No entities yet_")

    with col2:
        st.markdown("#### Events")
        if mind.events_graph.events:
            for ev in mind.events_graph.events.values():
                names = [
                    mind.bridge.entities[p].name
                    for p in ev.participants
                    if p in mind.bridge.entities
                ]
                st.markdown(
                    f"- **{ev.place or 'Event'}** → {', '.join(names)}"
                )
        else:
            st.markdown("_No shared events yet_")

    with col3:
        st.markdown("#### Coherence")
        try:
            coh = mind.coherence.evaluate(text="", tags=[])
            st.metric("Score", coh.get("score", "—"))
        except Exception:
            st.metric("Score", "—")
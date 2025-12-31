import streamlit as st
from a7do.mind import A7DOMind

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="A7DO Cognitive Interface",
    layout="centered",
)

st.title("🧠 A7DO Cognitive Interface")
st.caption("Grounded cognition · Explicit learning · Inspectable memory")

# -------------------------------------------------
# Session state
# -------------------------------------------------
if "mind" not in st.session_state:
    st.session_state.mind = A7DOMind()

if "history" not in st.session_state:
    st.session_state.history = []

mind: A7DOMind = st.session_state.mind

# -------------------------------------------------
# Identity panel (safe)
# -------------------------------------------------
with st.expander("🧬 Identity", expanded=True):
    identity = mind.identity
    st.markdown(
        f"""
**Name:** {getattr(identity, "name", "A7DO")}  
**Creator:** {getattr(identity, "creator", "Unknown")}  
**Type:** {getattr(identity, "being_type", "Cognitive System")}
"""
    )

# -------------------------------------------------
# Chat input
# -------------------------------------------------
st.subheader("💬 Speak to A7DO")

user_text = st.text_input(
    "Enter a message",
    placeholder="Try: 'My name is Alex Macleod' or 'Xena is my dog'",
)

if user_text:
    result = mind.process(user_text)
    st.session_state.history.append(
        {
            "user": user_text,
            "result": result,
        }
    )

# -------------------------------------------------
# Conversation display
# -------------------------------------------------
if st.session_state.history:
    st.subheader("🗨️ Conversation")

    for turn in st.session_state.history[::-1]:
        st.markdown(f"**You:** {turn['user']}")

        answer = turn["result"].get("answer", "—")
        st.markdown(f"**A7DO:** {answer}")

        tags = turn["result"].get("tags")
        if tags:
            st.caption(f"Tags: {', '.join(tags)}")

        coherence = turn["result"].get("coherence")
        if isinstance(coherence, dict):
            score = coherence.get("score")
            if score is not None:
                st.caption(f"Coherence score: {score}")

        st.divider()

# -------------------------------------------------
# Background density (debug / insight)
# -------------------------------------------------
with st.expander("🌫️ Background Density"):
    bg = mind.background
    summary = {}

    for attr in ("queue_len", "working_len", "last_queue_item_tags"):
        if hasattr(bg, attr):
            summary[attr] = getattr(bg, attr)

    if summary:
        st.json(summary)
    else:
        st.caption("No background activity yet.")

# -------------------------------------------------
# Pending entities (read-only here)
# -------------------------------------------------
with st.expander("🧩 Pending Entities"):
    pending = mind.bridge.pending
    if not pending:
        st.caption("No pending entities.")
    else:
        for p in pending.values():
            st.write(
                f"• **{p.name}** "
                f"(confidence={p.confidence:.2f}, seen={p.count})"
            )

# -------------------------------------------------
# Entity graph (read-only here)
# -------------------------------------------------
with st.expander("🗂️ Entity Graph"):
    entities = mind.bridge.entities
    if not entities:
        st.caption("No promoted entities yet.")
    else:
        for e in entities.values():
            st.markdown(
                f"""
**{e.name}**  
Type: `{e.kind}`  
Aliases: {", ".join(e.aliases) if e.aliases else "—"}
"""
            )

# -------------------------------------------------
# System signal
# -------------------------------------------------
with st.expander("📡 System Signal"):
    signal = getattr(mind, "_last_signal", None)
    if signal:
        st.json(signal)
    else:
        st.caption("No system signals emitted yet.")
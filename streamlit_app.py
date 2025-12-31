import streamlit as st
import time

from a7do.mind import A7DOMind

# -------------------------------------------------
# Page config
# -------------------------------------------------

st.set_page_config(
    page_title="A7DO Cognitive Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🧠 A7DO – Flow Cognitive Engine")
st.caption("Event-based learning · Entity grounding · Reflection · Sleep")

# -------------------------------------------------
# Session state
# -------------------------------------------------

if "mind" not in st.session_state:
    st.session_state.mind = A7DOMind()

if "history" not in st.session_state:
    st.session_state.history = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

mind: A7DOMind = st.session_state.mind

# -------------------------------------------------
# Sidebar – Mind State
# -------------------------------------------------

with st.sidebar:
    st.header("🧩 Mind State")

    # -----------------------------
    # Identity (Option A: UI only)
    # -----------------------------
    st.subheader("🧬 Identity")

    identity = mind.identity
    st.markdown(
        f"""
**Name:** {identity.name}  
**Creator:** {identity.creator}  
**Type:** {identity.being_type}
"""
    )

    st.divider()

    # -----------------------------
    # Coherence
    # -----------------------------
    if st.session_state.last_result:
        coh = st.session_state.last_result.get("coherence", {})
        st.metric("Coherence Score", coh.get("score", "—"))
        if coh.get("label"):
            st.caption(coh["label"])

    st.divider()

    # -----------------------------
    # Sleep / system signal
    # -----------------------------
    if st.session_state.last_result:
        signal = st.session_state.last_result.get("signal")
        if signal:
            if signal["kind"] == "SLEEP":
                st.info(f"🛌 {signal['message']}")
            else:
                st.caption(f"{signal['kind']}: {signal['message']}")

    st.divider()

    # -----------------------------
    # Reflections (awareness)
    # -----------------------------
    st.subheader("🪞 Reflections")

    if st.session_state.last_result:
        reflections = st.session_state.last_result.get("reflections", {})
        if not reflections:
            st.caption("No active reflections yet.")
        else:
            for entity_id, refls in reflections.items():
                if not refls:
                    continue
                st.markdown(f"**Entity:** `{entity_id}`")
                for r in refls:
                    st.write(
                        f"- {r['pattern']} "
                        f"(score={r['score']}, band={r['band']})"
                    )

    st.divider()

    # -----------------------------
    # Pending entities (bridge)
    # -----------------------------
    st.subheader("🧩 Pending Entities")

    if st.session_state.last_result:
        pending = st.session_state.last_result.get("pending_entities", [])
        if not pending:
            st.caption("No pending entities.")
        else:
            for p in pending:
                st.write(
                    f"• **{p['name']}** "
                    f"(guess={p['kind_guess']}, "
                    f"confidence={p['confidence']})"
                )

    st.divider()

    # -----------------------------
    # Recent interaction history
    # -----------------------------
    st.subheader("📚 Recent Inputs")
    for h in st.session_state.history[-5:][::-1]:
        st.caption(h["text"])

# -------------------------------------------------
# Main interaction area
# -------------------------------------------------

st.subheader("💬 Interaction")

user_text = st.text_input(
    "Say something to A7DO",
    placeholder="Hello…",
    key="input_text"
)

send = st.button("Send")

# -------------------------------------------------
# Process input
# -------------------------------------------------

if send and user_text.strip():
    with st.spinner("A7DO is processing…"):
        result = mind.process(user_text)

    st.session_state.history.append({"text": user_text})
    st.session_state.last_result = result

    # tiny pause for cognitive feel
    time.sleep(0.15)

# -------------------------------------------------
# Response
# -------------------------------------------------

if st.session_state.last_result:
    st.subheader("🗣️ A7DO Response")
    st.markdown(st.session_state.last_result["answer"])

# -------------------------------------------------
# Inspector / Debug
# -------------------------------------------------

with st.expander("🔍 Mind Inspector", expanded=False):
    if st.session_state.last_result:
        st.json(st.session_state.last_result)
    else:
        st.caption("No activity yet.")
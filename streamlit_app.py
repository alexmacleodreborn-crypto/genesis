import streamlit as st
import time

from a7do.mind import A7DOMind

# ----------------------------------------
# Page configuration
# ----------------------------------------

st.set_page_config(
    page_title="A7DO Cognitive Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🧠 A7DO – Flow Cognitive Engine")
st.caption("Event-based learning • Reflection • Sleep • Coherence")

# ----------------------------------------
# Session state initialisation
# ----------------------------------------

if "mind" not in st.session_state:
    st.session_state.mind = A7DOMind()

if "history" not in st.session_state:
    st.session_state.history = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None


mind: A7DOMind = st.session_state.mind

# ----------------------------------------
# Sidebar – Mind State
# ----------------------------------------

with st.sidebar:
    st.header("🧩 Mind State")

    # Identity panel
    st.subheader("Identity")
    identity = mind.identity

st.markdown("### 🧬 Identity")
st.markdown(f"""
**Name:** {identity.name}  
**Creator:** {identity.creator}  
**Type:** {identity.being_type}
""")
    st.divider()

    # Coherence
    if st.session_state.last_result:
        coh = st.session_state.last_result.get("coherence", {})
        st.metric(
            "Coherence Score",
            coh.get("score", "—")
        )
        st.caption(coh.get("label", ""))

    st.divider()

    # Sleep / thinking signal
    if st.session_state.last_result:
        signal = st.session_state.last_result.get("signal")
        if signal:
            if signal["kind"] == "SLEEP":
                st.info(f"🛌 {signal['message']}")
            else:
                st.caption(f"{signal['kind']}: {signal['message']}")

    st.divider()

    # Reflections (awareness)
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

    # Recent memory (raw)
    st.subheader("📚 Recent Events")
    for h in st.session_state.history[-5:][::-1]:
        st.caption(f"[{h['event_id']}] {h['text']}")

# ----------------------------------------
# Main interaction area
# ----------------------------------------

st.subheader("💬 Interaction")

user_text = st.text_input(
    "Say something to A7DO",
    placeholder="Hello…",
    key="input_text"
)

send = st.button("Send")

# ----------------------------------------
# Process input
# ----------------------------------------

if send and user_text.strip():
    with st.spinner("A7DO is processing…"):
        result = mind.process(user_text)

    # Save history
    st.session_state.history.append({
        "text": user_text,
        "event_id": result["event_id"]
    })

    st.session_state.last_result = result

    # Small pause for cognitive feel
    time.sleep(0.2)

# ----------------------------------------
# Display response
# ----------------------------------------

if st.session_state.last_result:
    st.subheader("🗣️ A7DO Response")
    st.markdown(st.session_state.last_result["answer"])

# ----------------------------------------
# Inspector / Debug View
# ----------------------------------------

with st.expander("🔍 Mind Inspector", expanded=False):
    if st.session_state.last_result:
        st.json(st.session_state.last_result)
    else:
        st.caption("No activity yet.")
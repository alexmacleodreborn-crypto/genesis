import streamlit as st
import matplotlib.pyplot as plt

# --------------------------------------------------
# Imports (constructors only, no side effects)
# --------------------------------------------------

from a7do.identity import Identity
from a7do.emotional_state import EmotionalState
from a7do.memory import Memory
from a7do.development import Development
from a7do.multi_agent import MultiAgent
from a7do.childhood import Childhood
from a7do.mind import A7DOMind

# --------------------------------------------------
# Streamlit configuration
# --------------------------------------------------

st.set_page_config(
    page_title="A7DO Cognitive Interface",
    layout="wide"
)

st.title("🧠 A7DO — Cognitive Interface")
st.caption("A modular, coherence-driven cognitive engine")

# --------------------------------------------------
# Session-safe initialization (runs ONCE)
# --------------------------------------------------

if "mind" not in st.session_state:
    identity = Identity()
    emotion = EmotionalState()
    memory = Memory()
    development = Development()
    multi_agent = MultiAgent()
    childhood = Childhood()

    mind = A7DOMind(
        identity=identity,
        emotion=emotion,
        memory=memory,
        development=development,
        multi_agent=multi_agent,
        childhood=childhood
    )

    # Expose all components for inspector pages
    st.session_state["identity"] = identity
    st.session_state["emotion"] = emotion
    st.session_state["memory"] = memory
    st.session_state["development"] = development
    st.session_state["multi_agent"] = multi_agent
    st.session_state["childhood"] = childhood
    st.session_state["mind"] = mind

# --------------------------------------------------
# Recover shared state
# --------------------------------------------------

identity    = st.session_state["identity"]
emotion     = st.session_state["emotion"]
memory      = st.session_state["memory"]
development = st.session_state["development"]
childhood   = st.session_state["childhood"]
mind        = st.session_state["mind"]

# --------------------------------------------------
# Sidebar — Character Panel
# --------------------------------------------------

with st.sidebar:
    st.header("🧬 Character Panel")
    st.markdown(identity.panel())
    st.markdown(emotion.panel())
    st.markdown(development.panel())

    st.divider()

    st.header("🗂 Memory (Summary)")
    st.json(memory.summary())

# --------------------------------------------------
# Main Interaction
# --------------------------------------------------

user_text = st.text_input("Speak to A7DO")

if user_text:
    # Run cognition
    result = mind.process(user_text)

    # --------------------------------------------------
    # Cognitive Timeline
    # --------------------------------------------------

    st.subheader("🧠 Cognitive Activity")
    for event in result["events"]:
        st.code(event)

    # --------------------------------------------------
    # Mind Path
    # --------------------------------------------------

    st.subheader("🧭 Mind Path")
    st.write(" → ".join(result.get("path", [])))

    # --------------------------------------------------
    # Coherence
    # --------------------------------------------------

    st.subheader("✅ Coherence")
    coh = result.get("coherence", {})
    st.metric("Coherence Score", coh.get("score", "—"))
    st.write(f"Status: **{coh.get('label', '—')}**")

    # --------------------------------------------------
    # Reasoning Signals (Z–Σ)
    # --------------------------------------------------

    signals = result.get("signals")

    if signals and signals.get("z") and signals.get("sigma"):
        st.subheader(f"📈 Reasoning Signals (Z–Σ) — {signals.get('mode')}")

        z = signals["z"]
        sigma = signals["sigma"]

        fig, ax = plt.subplots(2, 1, figsize=(9, 5))

        ax[0].plot(z, label="Z (Inhibition)")
        ax[0].plot(sigma, label="Σ (Exploration)")
        ax[0].legend()
        ax[0].set_title("Constraint vs Exploration")

        coherence_trace = [s / (zv + 1e-3) for s, zv in zip(sigma, z)]
        ax[1].plot(coherence_trace)
        ax[1].axhline(0.6, linestyle="--", color="yellow")
        ax[1].set_title("Coherence Gate (Safe to Speak)")

        st.pyplot(fig)
        
    st.subheader("🗣 Speech Gate")
    st.write(f"Action: **{result.get('speech_action','—')}**")
    # --------------------------------------------------
    # Final Output
    # --------------------------------------------------

    st.subheader("💬 A7DO Response")
    st.markdown(f"> {result['answer']}")

    # --------------------------------------------------
    # Childhood Learning (visible only in early stages)
    # --------------------------------------------------

    if development.STAGES[development.index] in ["Birth", "Learning"]:
        st.subheader("🧒 Childhood Learning")

        summary = childhood.summary()

        if summary["active"]:
            st.info(
                f"Learning burst active — "
                f"{summary['seconds_remaining']}s remaining"
            )

        if summary["imprints"]:
            st.json(summary["imprints"])
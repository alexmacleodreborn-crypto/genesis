import streamlit as st
import matplotlib.pyplot as plt

# --------------------------------------------------
# Import ONLY concrete modules (no circular imports)
# --------------------------------------------------

from a7do.identity import Identity
from a7do.emotional_state import EmotionalState
from a7do.memory import Memory
from a7do.development import Development
from a7do.multi_agent import MultiAgent
from a7do.childhood import Childhood
from a7do.mind import A7DOMind

# --------------------------------------------------
# Streamlit config
# --------------------------------------------------

st.set_page_config(
    page_title="A7DO Cognitive Interface",
    layout="wide"
)

st.title("🧠 A7DO — Cognitive Interface")

# --------------------------------------------------
# Session-safe initialization (ONLY ONCE)
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

    # Store EVERYTHING for other pages (Inspector)
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
multi_agent = st.session_state["multi_agent"]
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

    st.header("🗂 Memory")
    st.json(memory.summary())

# --------------------------------------------------
# Main Interaction
# --------------------------------------------------

user_text = st.text_input("Speak to A7DO")

if user_text:

    result = mind.process(user_text)
    
    st.subheader("🧭 Mind Path")
st.write(" → ".join(result.get("path", [])))

st.subheader("✅ Coherence")
coh = result.get("coherence") or {}
st.metric("Coherence Score", coh.get("score", "—"))
st.write(f"Status: **{coh.get('label','—')}**")

    # ----------------------------------------------
    # Cognitive Timeline
    # ----------------------------------------------

st.subheader("🧠 Cognitive Activity")

for event in result["events"]:
    st.code(event)

    # ----------------------------------------------
    # Reasoning Signals (Z–Σ)
    # ----------------------------------------------

    signals = result.get("signals", {})

    if signals:
        z = signals.get("z", [])
        sigma = signals.get("sigma", [])
        mode = signals.get("mode", "unknown")

        if z and sigma:
            st.subheader(f"📈 Thought Dynamics ({mode})")

            fig, ax = plt.subplots(2, 1, figsize=(9, 5))

            ax[0].plot(z, label="Z (Inhibition)")
            ax[0].plot(sigma, label="Σ (Chaos)")
            ax[0].legend()
            ax[0].set_title("Constraint vs Exploration")

            coherence = [s / (zv + 1e-3) for s, zv in zip(sigma, z)]
            ax[1].plot(coherence)
            ax[1].axhline(0.6, linestyle="--", color="yellow")
            ax[1].set_title("Coherence Gate (Safe to Speak)")

            st.pyplot(fig)

    # ----------------------------------------------
    # Final Output
    # ----------------------------------------------

    st.subheader("💬 A7DO Response")
    st.markdown(f"> {result['answer']}")

    # ----------------------------------------------
    # Childhood Learning Status (optional visibility)
    # ----------------------------------------------

    if development.STAGES[development.index] in ["Birth", "Learning"]:
        st.subheader("🧒 Childhood Learning")

        summary = childhood.summary()

        if summary["active"]:
            st.info(
                f"Childhood learning active "
                f"({summary['seconds_remaining']}s remaining)"
            )

        if summary["imprints"]:
            st.json(summary["imprints"])
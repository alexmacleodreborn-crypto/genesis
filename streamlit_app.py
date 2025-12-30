import streamlit as st
import matplotlib.pyplot as plt

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
st.caption("A coherence-regulated, multi-domain cognitive engine")

# --------------------------------------------------
# Session-safe initialization
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

    st.session_state.update({
        "identity": identity,
        "emotion": emotion,
        "memory": memory,
        "development": development,
        "multi_agent": multi_agent,
        "childhood": childhood,
        "mind": mind,
    })

identity    = st.session_state["identity"]
emotion     = st.session_state["emotion"]
memory      = st.session_state["memory"]
development = st.session_state["development"]
childhood   = st.session_state["childhood"]
mind        = st.session_state["mind"]

# --------------------------------------------------
# Sidebar — System State
# --------------------------------------------------

with st.sidebar:
    st.header("🧬 System State")

    st.subheader("Identity")
    st.json({
        "user_name": identity.user_name,
        "system_name": identity.system_name,
        "creator": identity.creator
    })

    st.subheader("Emotion")
    st.json(emotion.export())

    st.subheader("Development")
    st.json({
        "stage": development.STAGES[development.index],
        "index": development.index
    })

    st.divider()

    st.header("👤 Learned Profiles")
    st.json(mind.profiles.summary())

    st.divider()

    st.header("🌫 Background Density")
    st.json(mind.density.stats())

    st.divider()

    st.header("🗂 Memory Summary")
    st.json(memory.summary())

# --------------------------------------------------
# Main Interaction
# --------------------------------------------------

user_text = st.text_input("Speak to A7DO")

if user_text:
    result = mind.process(user_text)

    # -------------------------
    # Cognitive Timeline
    # -------------------------
    st.subheader("🧠 Cognitive Activity")
    for event in result.get("events", []):
        st.code(event)

    # -------------------------
    # Mind Path
    # -------------------------
    st.subheader("🧭 Mind Path")
    st.write(" → ".join(result.get("path", [])))

    # -------------------------
    # Coherence (SAFE)
    # -------------------------
    st.subheader("✅ Coherence")

    coh = result.get("coherence")

    if coh:
        st.metric("Coherence Score", round(coh.get("score", 0.0), 3))
        st.write(f"Status: **{coh.get('label', '—')}**")
    else:
        st.write("Coherence not evaluated for this path.")

    # -------------------------
    # Speech Gate
    # -------------------------
    st.subheader("🗣 Speech Gate")
    st.write(f"Action: **{result.get('speech_action', '—')}**")

    # -------------------------
    # Background Density
    # -------------------------
    st.subheader("🌫 Background Density")
    st.json(result.get("density", {}))

    # -------------------------
    # Reasoning Signals (Z–Σ)
    # -------------------------
    signals = result.get("signals")

    if signals and signals.get("z") and signals.get("sigma"):
        st.subheader(f"📈 Reasoning Signals (Z–Σ) — {signals.get('mode')}")

        z = signals["z"]
        sigma = signals["sigma"]

        fig, ax = plt.subplots(2, 1, figsize=(9, 5))

        ax[0].plot(z, label="Z (Constraint)")
        ax[0].plot(sigma, label="Σ (Exploration)")
        ax[0].legend()
        ax[0].set_title("Constraint vs Exploration")

        coherence_trace = [s / (zv + 1e-3) for s, zv in zip(sigma, z)]
        ax[1].plot(coherence_trace)
        ax[1].axhline(0.6, linestyle="--", color="yellow")
        ax[1].set_title("Coherence Gate")

        st.pyplot(fig)

    # -------------------------
    # Final Output
    # -------------------------
    st.subheader("💬 A7DO Response")
    st.markdown(f"> {result['answer']}")

    # -------------------------
    # Childhood Learning
    # -------------------------
    if development.STAGES[development.index] in ["Birth", "Learning"]:
        st.subheader("🧒 Childhood Learning")
        st.json(childhood.summary())
import streamlit as st
import matplotlib.pyplot as plt

from a7do.identity import Identity
from a7do.emotional_state import EmotionalState
from a7do.memory import Memory
from a7do.development import Development
from a7do.multi_agent import MultiAgent
from a7do.childhood import Childhood
from a7do.mind import A7DOMind

st.set_page_config(page_title="A7DO Cognitive Interface", layout="wide")

st.title("🧠 A7DO — Cognitive Interface")
st.caption("Coherence-regulated cognition with confidence-based learning")

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
        "last_result": None,
    })

identity = st.session_state["identity"]
emotion = st.session_state["emotion"]
memory = st.session_state["memory"]
development = st.session_state["development"]
childhood = st.session_state["childhood"]
mind = st.session_state["mind"]

with st.sidebar:
    st.header("🧬 System State")

    st.subheader("Identity")
    st.json({
        "user_name": identity.user_name,
        "system_name": getattr(identity, "system_name", "A7DO"),
        "creator": getattr(identity, "creator", "Alex Macleod"),
    })

    st.subheader("Emotion")
    st.json(emotion.export())

    st.subheader("Development")
    st.json({
        "stage": development.STAGES[development.index],
        "index": development.index
    })

    st.divider()

    st.header("🌫 Background Density")
    st.json(mind.density.stats())

    st.divider()

    st.header("🗂 Memory Summary")
    st.json(memory.summary())

    st.divider()

    st.header("👤 Profiles")
    st.json(mind.profiles.summary())

    st.divider()

    st.header("✅ Learning Confidence")
    st.write("**Candidates** = waiting to be confirmed")
    st.write("**Facts** = promoted stable beliefs")


user_text = st.text_input("Speak to A7DO")

if user_text:
    result = mind.process(user_text)
    st.session_state["last_result"] = result

result = st.session_state.get("last_result")

if result:
    st.subheader("🧠 Cognitive Activity")
    for event in result.get("events", []):
        st.code(event)

    st.subheader("🧭 Mind Path")
    st.write(" → ".join(result.get("path", [])))

    st.subheader("✅ Coherence")
    coh = result.get("coherence")
    if coh:
        st.metric("Coherence Score", round(coh.get("score", 0.0), 3))
        st.write(f"Status: **{coh.get('label', '—')}**")
    else:
        st.write("Coherence not evaluated for this path.")

    st.subheader("🧠 Learning Confidence")
    col1, col2 = st.columns(2)

    with col1:
        st.write("### Candidates")
        st.json(result.get("candidates", {}))

    with col2:
        st.write("### Facts (Promoted)")
        st.json(result.get("facts", {}))

    st.subheader("🗣 Speech Gate")
    st.write(f"Action: **{result.get('speech_action', '—')}**")

    st.subheader("🌫 Background Density State")
    st.json(result.get("density", {}))

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

    st.subheader("💬 A7DO Response")
    st.markdown(f"> {result['answer']}")

    if development.STAGES[development.index] in ["Birth", "Learning"]:
        st.subheader("🧒 Childhood Learning")
        st.json(childhood.summary())
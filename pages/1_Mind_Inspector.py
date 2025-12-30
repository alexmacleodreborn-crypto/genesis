import streamlit as st
import matplotlib.pyplot as plt

from a7do.childhood import Childhood
from a7do.identity import Identity
from a7do.emotional_state import EmotionalState
from a7do.memory import Memory
from a7do.development import Development
from a7do.multi_agent import MultiAgent
from a7do.mind import A7DOMind

st.set_page_config(page_title="A7DO – Mind Inspector", layout="wide")

st.title("🧠 A7DO Mind Inspector")
st.caption("Read-only inspection of the cognitive system state")

# ------------------------------------------------------------------
# IMPORTANT:
# This inspector creates NO new cognition.
# It only reflects what exists in session state.
# ------------------------------------------------------------------

# Recover or create shared state
if "identity" not in st.session_state:
    st.warning("No cognitive session detected yet. Run A7DO first.")
    st.stop()

identity = st.session_state["identity"]
emotion = st.session_state["emotion"]
memory = st.session_state["memory"]
development = st.session_state["development"]
multi_agent = st.session_state["multi_agent"]
mind = st.session_state["mind"]
childhood = st.session_state.get("childhood")

# ------------------------------------------------------------------
# IDENTITY
# ------------------------------------------------------------------

st.header("🧬 Identity")

st.markdown(f"""
- **System:** {identity.system_name}
- **Creator:** {identity.creator}
- **User:** {identity.user_name or "Unknown"}
""")

# ------------------------------------------------------------------
# EMOTIONAL STATE
# ------------------------------------------------------------------

st.header("❤️ Emotional State")

st.json(emotion.export())

# ------------------------------------------------------------------
# DEVELOPMENT
# ------------------------------------------------------------------

st.header("🌱 Development")

st.markdown(f"**Current Stage:** {development.STAGES[development.index]}")

# ------------------------------------------------------------------
# MEMORY
# ------------------------------------------------------------------

st.header("🗂 Memory")

st.metric("Total Memory Entries", len(memory.entries))

if memory.entries:
    st.subheader("Recent Memory")
    st.json(memory.recent(10))
else:
    st.info("No memories stored yet.")

# ------------------------------------------------------------------
# REASONING SIGNALS
# ------------------------------------------------------------------

st.header("📈 Reasoning Signals (Z–Σ)")

signals = multi_agent.last_signals

if signals:
    z = signals.get("z", [])
    sigma = signals.get("sigma", [])

    if z and sigma:
        fig, ax = plt.subplots(2, 1, figsize=(9, 5))

        ax[0].plot(z, label="Z (Inhibition)")
        ax[0].plot(sigma, label="Σ (Chaos)")
        ax[0].legend()
        ax[0].set_title("Neural Physics: Thought Shape")

        coherence = [s / (zv + 1e-3) for s, zv in zip(sigma, z)]
        ax[1].plot(coherence)
        ax[1].axhline(0.6, linestyle="--", color="yellow")
        ax[1].set_title("Consciousness Gate (Safe to Speak)")

        st.pyplot(fig)
    else:
        st.info("Signals present but empty.")
else:
    st.info("No reasoning signals yet.")

# ------------------------------------------------------------------
# COGNITIVE TIMELINE
# ------------------------------------------------------------------

st.header("🧠 Cognitive Timeline")

if mind.events:
    for e in mind.events:
        st.code(e)
else:
    st.info("No cognitive events recorded yet.")
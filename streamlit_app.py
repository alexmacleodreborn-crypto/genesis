import streamlit as st
import matplotlib.pyplot as plt

from a7do.identity import Identity
from a7do.emotional_state import EmotionalState
from a7do.memory import Memory
from a7do.development import Development
from a7do.multi_agent import MultiAgent
from a7do.mind import A7DOMind

st.set_page_config(page_title="A7DO", layout="wide")

identity = Identity()
emotion = EmotionalState()
memory = Memory()
development = Development()
multi_agent = MultiAgent()

mind = A7DOMind(identity, emotion, memory, development, multi_agent)

with st.sidebar:
    st.header("🧠 A7DO")
    st.markdown(identity.character_panel())
    st.markdown(emotion.character_panel())
    st.markdown(development.character_panel())
    st.json(memory.summary())

st.title("A7DO Cognitive Interface")

user_input = st.text_input("Speak to A7DO")

if user_input:
    result = mind.process(user_input)

    st.subheader("🧬 Cognitive Activity")
    for event in result["events"]:
        st.markdown(f"**[{event.phase}]** {event.message}")

    if result["reasoning"]:
        z = result["reasoning"]["z"]
        sigma = result["reasoning"]["sigma"]

        fig, ax = plt.subplots(2, 1, figsize=(8, 5))
        ax[0].plot(z, label="Inhibition (Z)")
        ax[0].plot(sigma, label="Chaos (Σ)")
        ax[0].legend()

        coherence = [s / (zv + 1e-3) for s, zv in zip(sigma, z)]
        ax[1].plot(coherence)
        ax[1].axhline(0.6, linestyle="--", color="yellow")
        st.pyplot(fig)

    st.subheader("💬 Final Answer")
    st.markdown(f"> {result['answer']}\n\n_Thought process complete._")
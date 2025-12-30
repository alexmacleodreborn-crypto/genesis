import streamlit as st
import matplotlib.pyplot as plt

from a7do.childhood import Childhood
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
childhood = Childhood()

mind = A7DOMind(identity, emotion, memory, development, multi_agent, childhood)st.session_state["identity"] = identity
st.session_state["emotion"] = emotion
st.session_state["memory"] = memory
st.session_state["development"] = development
st.session_state["multi_agent"] = multi_agent
st.session_state["mind"] = mind
st.session_state["childhood"] = childhood

with st.sidebar:
    st.header("🧠 A7DO")
    st.markdown(identity.panel())
    st.markdown(emotion.panel())
    st.markdown(development.panel())
    st.json(memory.summary())

st.title("A7DO Cognitive Interface")

text = st.text_input("Speak to A7DO")

if text:
    result = mind.process(text)

    st.subheader("🧬 Cognitive Activity")
    for e in result["events"]:
        st.write(e)

    if result["signals"]:
        z = result["signals"]["z"]
        sigma = result["signals"]["sigma"]

        fig, ax = plt.subplots(2, 1, figsize=(8, 5))
        ax[0].plot(z, label="Z (Inhibition)")
        ax[0].plot(sigma, label="Σ (Chaos)")
        ax[0].legend()

        coherence = [s / (zv + 1e-3) for s, zv in zip(sigma, z)]
        ax[1].plot(coherence)
        ax[1].axhline(0.6, linestyle="--", color="yellow")

        st.pyplot(fig)

    st.subheader("💬 Final Answer")
    st.markdown(f"> {result['answer']}")
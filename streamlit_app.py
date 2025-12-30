import streamlit as st
from a7do.identity import Identity
from a7do.emotional_state import EmotionalState
from a7do.memory import Memory
from a7do.development import Development
from a7do.multi_agent import MultiAgent
from a7do.childhood import Childhood
from a7do.mind import A7DOMind

st.set_page_config(layout="wide")
st.title("🧠 A7DO — Entity & Identity System")

if "mind" not in st.session_state:
    mind = A7DOMind(
        identity=Identity(),
        emotion=EmotionalState(),
        memory=Memory(),
        development=Development(),
        multi_agent=MultiAgent(),
        childhood=Childhood()
    )
    st.session_state.mind = mind
    st.session_state.last = None

mind = st.session_state.mind

text = st.text_input("Speak")

if text:
    st.session_state.last = mind.process(text)

if st.session_state.last:
    r = st.session_state.last

    st.subheader("Answer")
    st.write(r["answer"])

    st.subheader("Entity Graph")
    st.json(r["entities"])

    st.subheader("Entity Facts")
    st.json(r["facts"])

    st.subheader("Mind Path")
    st.write(" → ".join(r["path"]))
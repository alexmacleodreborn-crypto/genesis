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
st.caption("Developmental cognition with entity grounding")

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
        "mind": mind,
        "last_result": None,
    })

mind = st.session_state["mind"]
identity = st.session_state["identity"]
emotion = st.session_state["emotion"]
memory = st.session_state["memory"]
development = st.session_state["development"]

with st.sidebar:
    st.header("🧬 System State")

    st.subheader("Identity")
    st.json({
        "user": identity.user_name,
        "creator": identity.creator,
        "system": identity.system_name
    })

    st.subheader("Development")
    st.json({
        "stage": development.STAGES[development.index],
        "index": development.index
    })

    st.subheader("Foundational Language")
    st.json(mind.curriculum.peek_progress())

    if mind.last_curriculum_packet:
        st.write("Latest language drip")
        st.json(mind.last_curriculum_packet)

    st.subheader("🧩 Entity Graph")
    st.json(mind.entities.summary())

    st.subheader("🌫 Background Density")
    st.json(mind.density.stats())

    st.subheader("🗂 Memory")
    st.json(memory.summary())

user_text = st.text_input("Speak to A7DO")

if user_text:
    st.session_state["last_result"] = mind.process(user_text)

result = st.session_state.get("last_result")

if result:
    st.subheader("🧠 Cognitive Activity")
    for e in result["events"]:
        st.code(e)

    st.subheader("🧭 Mind Path")
    st.write(" → ".join(result["path"]))

    if result.get("coherence"):
        st.subheader("✅ Coherence")
        st.metric("Score", round(result["coherence"]["score"], 3))

    st.subheader("💬 Response")
    st.markdown(f"> {result['answer']}")
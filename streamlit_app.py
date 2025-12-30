import streamlit as st
import matplotlib.pyplot as plt

from a7do.identity import Identity
from a7do.emotional_state import EmotionalState
from a7do.memory import Memory
from a7do.development import Development
from a7do.multi_agent import MultiAgent
from a7do.childhood import Childhood
from a7do.mind import A7DOMind

st.set_page_config(layout="wide")
st.title("🧠 A7DO — Cognitive Identity Formation")

# --------------------------------------------------
# INIT
# --------------------------------------------------

if "mind" not in st.session_state:
    st.session_state.mind = A7DOMind(
        identity=Identity(),
        emotion=EmotionalState(),
        memory=Memory(),
        development=Development(),
        multi_agent=MultiAgent(),
        childhood=Childhood()
    )
    st.session_state.last = None

mind = st.session_state.mind

# --------------------------------------------------
# INPUT
# --------------------------------------------------

text = st.text_input("Speak to A7DO")

if text:
    st.session_state.last = mind.process(text)

# --------------------------------------------------
# OUTPUT
# --------------------------------------------------

if st.session_state.last:
    r = st.session_state.last

    st.subheader("💬 Response")
    st.write(r["answer"])

    st.subheader("🧠 Cognitive Activity")
    for e in r["events"]:
        st.code(e)

    st.subheader("🧭 Mind Path")
    st.write(" → ".join(r["path"]))

    st.subheader("🧩 Entity Graph")
    st.json(r["entities"])

    st.subheader("📊 Identity Formation")

    facts = r["facts"]
    candidates = facts.get("candidates", {})

    if candidates:
        labels = []
        counts = []

        for eid, items in candidates.items():
            for key, data in items.items():
                labels.append(key)
                counts.append(data["count"])

        fig, ax = plt.subplots()
        ax.barh(labels, counts)
        ax.set_xlabel("Repetition Count")
        ax.set_title("Candidate Identity Signals")

        st.pyplot(fig)
    else:
        st.caption("No identity candidates yet.")

    st.subheader("✅ Promoted Facts")
    st.json(facts.get("facts", {}))

    st.subheader("🏷 Aliases")
    st.json(facts.get("aliases", {}))
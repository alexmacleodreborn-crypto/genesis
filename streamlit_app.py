import streamlit as st
import matplotlib.pyplot as plt

from a7do.identity import Identity
from a7do.emotional_state import EmotionalState
from a7do.memory import Memory
from a7do.development import Development
from a7do.multi_agent import MultiAgent
from a7do.childhood import Childhood
from a7do.mind import A7DOMind

st.set_page_config(page_title="A7DO Flow Mind", layout="wide")
st.title("🧠 A7DO — Flow Learning & Mind-Pathing")

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

with st.sidebar:
    st.header("⚙️ Flow Controls")
    st.caption("Temporal binding window is set in EventMemory(bind_window_s).")

text = st.text_input("Speak to A7DO")

if text:
    st.session_state.last = mind.process(text)

r = st.session_state.last
if not r:
    st.info("Say something like: “My dog is called Xena. We are at the park. I feel excited. Xena is tied at the gate.”")
    st.stop()

st.subheader("💬 Response")
st.write(r["answer"])

st.subheader("🧠 Cognitive Activity")
for e in r["events"]:
    st.code(e)

st.subheader("🧭 Mind Path")
st.write(" → ".join(r["path"]))

col1, col2 = st.columns(2)

with col1:
    st.subheader("🧷 Current Event Frame")
    st.json(r.get("event"))

    st.subheader("📚 Recent Events")
    st.json(r.get("recent_events"))

with col2:
    st.subheader("📈 Flow Stats")
    st.json(r.get("event_stats"))

    st.subheader("🔁 Reoccurrence")
    st.json(r.get("reoccurrence"))

st.subheader("🧩 Entity Graph")
st.json(r.get("entities"))

st.subheader("🏷 Unbound Labels")
st.json(r.get("unbound_labels"))

st.subheader("✅ Entity Facts")
st.json(r.get("facts"))

# Simple chart: modalities / emotions / environments in current event
evt = r.get("event") or {}
modalities = evt.get("modalities", {})
emotions = evt.get("emotions", {})
env = evt.get("environments", {})

def bar_chart(title, data):
    if not data:
        st.caption(f"{title}: none detected.")
        return
    labels = list(data.keys())
    vals = list(data.values())
    fig, ax = plt.subplots()
    ax.bar(labels, vals)
    ax.set_title(title)
    st.pyplot(fig)

st.subheader("🎛 Event Signals")
bar_chart("Modalities", modalities)
bar_chart("Emotions", emotions)
bar_chart("Environments", env)